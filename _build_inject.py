#!/usr/bin/env python3
"""Inject a self-contained Flashcards + Vocabulary Quiz module into each lesson.
The module reads the page's existing global `vocabData` (arrays of [slovenian, english])
and reuses the global `speak()` for audio. Fully namespaced under `fcq` so it never
collides with a lesson's own scripts/styles. Idempotent: re-running won't duplicate."""

import sys

MARKER = "<!-- FCQ-COMPONENT -->"

SNIPPET = r"""<!-- FCQ-COMPONENT -->
<style>
.fcq-wrap{font-family:'Source Sans 3','Segoe UI',system-ui,sans-serif;
  --fcq-blue:#1a3a5c;--fcq-blue2:#2d6a9f;--fcq-pale:#eaf3fb;
  --fcq-green:#1e6b4a;--fcq-green-l:#e6f5ed;--fcq-red:#a3232b;--fcq-red-l:#fcebec;
  --fcq-gold:#c8960c;--fcq-border:#d4dde8;--fcq-muted:#5a6a7a;--fcq-ink:#16263a;}
.fcq-section{background:#fff;border:1px solid var(--fcq-border);border-radius:14px;
  margin:2rem 0;box-shadow:0 4px 18px rgba(16,40,70,.07);overflow:hidden;}
.fcq-head{padding:1rem 1.4rem;cursor:pointer;display:flex;justify-content:space-between;
  align-items:center;user-select:none;background:linear-gradient(135deg,var(--fcq-blue),#0d2440);
  color:#fff;}
.fcq-head h2{font-size:1.18rem;font-weight:700;margin:0;letter-spacing:.2px;}
.fcq-head h2 span{font-weight:400;color:#a8c8e8;font-size:.92rem;}
.fcq-toggle{font-size:1.1rem;color:#cfe2f4;transition:transform .2s;}
.fcq-section.fcq-collapsed .fcq-toggle{transform:rotate(-90deg);}
.fcq-body{padding:1.5rem 1.4rem 1.7rem;}
.fcq-section.fcq-collapsed .fcq-body{display:none;}

/* ---- progress bar ---- */
.fcq-bar{display:flex;align-items:center;gap:.8rem;margin-bottom:1rem;}
.fcq-stat{font-weight:700;color:var(--fcq-blue);font-size:.9rem;white-space:nowrap;
  background:var(--fcq-pale);padding:.25rem .6rem;border-radius:8px;}
.fcq-progress{flex:1;height:9px;background:#e3eaf2;border-radius:10px;overflow:hidden;}
.fcq-progress-fill{height:100%;width:0;background:linear-gradient(90deg,var(--fcq-blue2),var(--fcq-gold));
  border-radius:10px;transition:width .35s ease;}

/* ---- flashcard stage ---- */
.fcq-stage{display:flex;align-items:center;gap:.6rem;}
.fcq-card{flex:1;min-height:230px;perspective:0;position:relative;transform-style:preserve-3d;
  transition:transform .5s cubic-bezier(.4,.2,.2,1);cursor:pointer;}
.fcq-stage{perspective:1500px;}
.fcq-card.flipped{transform:rotateY(180deg);}
.fcq-face{position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;
  border-radius:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:1.4rem;text-align:center;border:2px solid var(--fcq-border);}
.fcq-front{background:linear-gradient(160deg,#fff,var(--fcq-pale));}
.fcq-back{background:linear-gradient(160deg,#fff,var(--fcq-green-l));transform:rotateY(180deg);
  border-color:#bfe0cd;}
.fcq-lang{font-size:.7rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
  color:var(--fcq-muted);margin-bottom:.5rem;}
.fcq-term{font-size:1.9rem;font-weight:800;color:var(--fcq-ink);line-height:1.2;word-break:break-word;}
.fcq-back .fcq-term{color:var(--fcq-green);}
.fcq-audio{margin-top:1rem;background:var(--fcq-blue);color:#fff;border:none;border-radius:50px;
  padding:.4rem 1rem;font-size:1rem;cursor:pointer;transition:transform .15s,background .15s;}
.fcq-audio:hover{transform:scale(1.06);background:var(--fcq-blue2);}
.fcq-nav{flex:0 0 auto;width:46px;height:46px;border-radius:50%;border:2px solid var(--fcq-border);
  background:#fff;color:var(--fcq-blue);font-size:1.6rem;line-height:1;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:.15s;}
.fcq-nav:hover{background:var(--fcq-blue);color:#fff;border-color:var(--fcq-blue);}
.fcq-hint{text-align:center;color:var(--fcq-muted);font-size:.8rem;margin:.8rem 0 .4rem;}
.fcq-hint b{color:var(--fcq-blue);}

.fcq-actions{display:flex;gap:.7rem;justify-content:center;margin:.6rem 0 1rem;flex-wrap:wrap;}
.fcq-btn{border:none;border-radius:10px;padding:.6rem 1.3rem;font-size:.95rem;font-weight:700;
  cursor:pointer;transition:transform .12s,box-shadow .15s;color:#fff;}
.fcq-btn:active{transform:scale(.96);}
.fcq-learning{background:var(--fcq-gold);}
.fcq-known-btn{background:var(--fcq-green);}
.fcq-btn:hover{box-shadow:0 4px 12px rgba(0,0,0,.18);}

.fcq-tools{display:flex;gap:.5rem;justify-content:center;flex-wrap:wrap;}
.fcq-chip{border:1.5px solid var(--fcq-border);background:#fff;border-radius:50px;
  padding:.35rem .9rem;font-size:.82rem;font-weight:600;color:var(--fcq-blue);cursor:pointer;
  transition:.15s;display:inline-flex;align-items:center;gap:.35rem;}
.fcq-chip:hover{border-color:var(--fcq-blue2);background:var(--fcq-pale);}
.fcq-filter-wrap{cursor:pointer;}
.fcq-filter-wrap input{accent-color:var(--fcq-blue);}

.fcq-done{text-align:center;padding:2rem 1rem;}
.fcq-done .big{font-size:2.2rem;font-weight:900;color:var(--fcq-green);margin-bottom:.4rem;}
.fcq-done .sub{color:var(--fcq-muted);}

/* ---- quiz ---- */
.fcq-quiz-intro{background:var(--fcq-pale);border-radius:10px;padding:.7rem 1rem;
  color:var(--fcq-ink);font-size:.92rem;margin-bottom:1.1rem;}
.fcq-q{border:1px solid var(--fcq-border);border-radius:12px;padding:1rem 1.1rem;margin-bottom:.9rem;
  background:#fff;}
.fcq-q-prompt{font-size:1.05rem;font-weight:700;color:var(--fcq-ink);margin-bottom:.7rem;
  display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;}
.fcq-q-num{color:var(--fcq-blue2);}
.fcq-q-mini{background:var(--fcq-blue);color:#fff;border:none;border-radius:6px;padding:.1rem .45rem;
  cursor:pointer;font-size:.85rem;}
.fcq-q-mini:hover{background:var(--fcq-blue2);}
.fcq-opts{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;}
.fcq-opt{border:2px solid var(--fcq-border);border-radius:9px;padding:.55rem .8rem;cursor:pointer;
  font-size:.92rem;background:#fff;transition:.12s;color:var(--fcq-ink);}
.fcq-opt:hover{border-color:var(--fcq-blue2);background:var(--fcq-pale);}
.fcq-opt.sel{border-color:var(--fcq-blue);background:var(--fcq-pale);font-weight:700;}
.fcq-opt.ok{border-color:var(--fcq-green);background:var(--fcq-green-l);color:var(--fcq-green);font-weight:700;}
.fcq-opt.bad{border-color:var(--fcq-red);background:var(--fcq-red-l);color:var(--fcq-red);}
.fcq-quiz-foot{display:flex;gap:.7rem;align-items:center;margin-top:.5rem;flex-wrap:wrap;}
.fcq-submit{background:var(--fcq-green);color:#fff;border:none;border-radius:10px;padding:.65rem 1.6rem;
  font-size:1rem;font-weight:700;cursor:pointer;transition:.15s;}
.fcq-submit:hover{box-shadow:0 4px 12px rgba(0,0,0,.18);}
.fcq-result{display:none;margin-top:1.1rem;text-align:center;background:var(--fcq-pale);
  border-radius:12px;padding:1.4rem;}
.fcq-result .big{font-size:2.4rem;font-weight:900;color:var(--fcq-blue);}
.fcq-result .pct{font-size:1.1rem;color:var(--fcq-muted);}
.fcq-result .grade{margin-top:.5rem;font-size:1.15rem;font-weight:700;}
@media(max-width:560px){.fcq-opts{grid-template-columns:1fr;}.fcq-term{font-size:1.5rem;}}
</style>
<script>
(function(){
  if (typeof vocabData === 'undefined' || !vocabData) return;
  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded',fn); }
  ready(function(){
    var host = document.querySelector('.container') || document.body;
    if (!host) return;

    /* ---- build a de-duplicated deck from all vocab groups ---- */
    var DECK = [], seen = {};
    Object.keys(vocabData).forEach(function(k){
      var arr = vocabData[k]; if(!Array.isArray(arr)) return;
      arr.forEach(function(p){
        if(!Array.isArray(p) || p.length<2) return;
        var sl=String(p[0]).trim(), en=String(p[1]).trim();
        if(!sl||!en) return;
        var id=sl+'|'+en; if(seen[id]) return; seen[id]=1;
        DECK.push({sl:sl,en:en});
      });
    });
    if (DECK.length < 4) return;

    function speakSL(sl){
      if (typeof speak !== 'function') return;
      var cands=[sl.replace(/\s*\/\s*/g,' ali '), sl.replace(/\//g,' ali '), sl];
      var key=cands[0];
      if (typeof AUDIO !== 'undefined' && AUDIO){ for(var i=0;i<cands.length;i++){ if(AUDIO[cands[i]]){ key=cands[i]; break; } } }
      try{ speak(key); }catch(e){}
    }
    function shuf(a){ for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t;} return a; }

    /* ---- markup ---- */
    var LKEY = 'fcq-known-' + (location.pathname.split('/').pop() || 'lesson');
    var wrap = document.createElement('div');
    wrap.className = 'fcq-wrap';
    wrap.innerHTML =
      '<div class="fcq-section" id="fcq-flashcards">'
      + '<div class="fcq-head"><h2>🃏 Besedne kartice <span>· Flashcards</span></h2><span class="fcq-toggle">▲</span></div>'
      + '<div class="fcq-body">'
      +   '<div class="fcq-bar"><div class="fcq-stat" id="fcq-pos">1 / 1</div>'
      +     '<div class="fcq-progress"><div class="fcq-progress-fill" id="fcq-fill"></div></div>'
      +     '<div class="fcq-stat" id="fcq-known">✅ 0</div></div>'
      +   '<div class="fcq-stage">'
      +     '<button class="fcq-nav fcq-prev" title="Prejšnja (←)">‹</button>'
      +     '<div class="fcq-card" id="fcq-card">'
      +       '<div class="fcq-face fcq-front" id="fcq-front"></div>'
      +       '<div class="fcq-face fcq-back" id="fcq-back"></div>'
      +     '</div>'
      +     '<button class="fcq-nav fcq-next" title="Naslednja (→)">›</button>'
      +   '</div>'
      +   '<div class="fcq-hint">Klikni kartico ali pritisni <b>preslednico</b> za obrat · puščice ← → za premikanje</div>'
      +   '<div class="fcq-actions">'
      +     '<button class="fcq-btn fcq-learning">🔁 Še se učim</button>'
      +     '<button class="fcq-btn fcq-known-btn">✅ Znam!</button>'
      +   '</div>'
      +   '<div class="fcq-tools">'
      +     '<button class="fcq-chip fcq-shuffle">🔀 Premešaj</button>'
      +     '<button class="fcq-chip fcq-dir">↔ SL → EN</button>'
      +     '<label class="fcq-chip fcq-filter-wrap"><input type="checkbox" class="fcq-filter"> Le neznane</label>'
      +     '<button class="fcq-chip fcq-reset">🗑 Ponastavi napredek</button>'
      +   '</div>'
      + '</div></div>'
      + '<div class="fcq-section" id="fcq-quiz">'
      + '<div class="fcq-head"><h2>🎯 Besedni izziv <span>· Vocabulary Quiz</span></h2><span class="fcq-toggle">▲</span></div>'
      + '<div class="fcq-body">'
      +   '<div class="fcq-quiz-intro">Naključnih <b id="fcq-qn">0</b> vprašanj iz besedišča te lekcije. Izberi pravilni prevod — ujemi čim več! 🏆</div>'
      +   '<div id="fcq-quiz-list"></div>'
      +   '<div class="fcq-quiz-foot"><button class="fcq-submit" id="fcq-quiz-submit">Oddaj odgovore</button>'
      +     '<button class="fcq-chip fcq-new-quiz">🔄 Nov test</button></div>'
      +   '<div class="fcq-result" id="fcq-quiz-result"></div>'
      + '</div></div>';
    host.appendChild(wrap);

    /* collapse toggles */
    wrap.querySelectorAll('.fcq-head').forEach(function(h){
      h.addEventListener('click', function(){ h.parentElement.classList.toggle('fcq-collapsed'); });
    });

    /* nav-pill links (lessons that use them) */
    var pills = document.querySelector('.nav-pills');
    if (pills){
      var a1=document.createElement('a'); a1.href='#fcq-flashcards'; a1.textContent='Kartice';
      var a2=document.createElement('a'); a2.href='#fcq-quiz'; a2.textContent='Besedni test';
      pills.appendChild(a1); pills.appendChild(a2);
    }

    /* ================= FLASHCARDS ================= */
    var known = {};
    try{ known = JSON.parse(localStorage.getItem(LKEY)||'{}') || {}; }catch(e){ known={}; }
    var dir='sl2en', onlyLearning=false, view=[], pos=0, flipped=false;
    var cardEl=wrap.querySelector('#fcq-card');
    var frontEl=wrap.querySelector('#fcq-front');
    var backEl=wrap.querySelector('#fcq-back');
    var posEl=wrap.querySelector('#fcq-pos');
    var fillEl=wrap.querySelector('#fcq-fill');
    var knownEl=wrap.querySelector('#fcq-known');
    var dirBtn=wrap.querySelector('.fcq-dir');

    function idOf(i){ return DECK[i].sl+'|'+DECK[i].en; }
    function knownCount(){ var n=0; for(var k in known){ if(known[k]) n++; } return n; }
    function saveKnown(){ try{ localStorage.setItem(LKEY, JSON.stringify(known)); }catch(e){} }

    function buildView(doShuffle){
      view=[];
      for(var i=0;i<DECK.length;i++){
        if(onlyLearning && known[idOf(i)]) continue;
        view.push(i);
      }
      if(!view.length) view=[]; /* allow empty -> done screen */
      if(doShuffle) shuf(view);
      pos=0; flipped=false;
    }

    function faceHTML(text, isSL, langLabel){
      var audio = isSL ? '<button class="fcq-audio" data-sl="'+text.replace(/"/g,'&quot;')+'">🔊 Poslušaj</button>' : '';
      return '<div class="fcq-lang">'+langLabel+'</div><div class="fcq-term">'+text+'</div>'+audio;
    }

    function render(){
      cardEl.classList.remove('flipped'); flipped=false;
      knownEl.textContent='✅ '+knownCount()+' / '+DECK.length;
      if(!view.length){
        posEl.textContent='0 / 0'; fillEl.style.width='100%';
        frontEl.innerHTML='<div class="fcq-done"><div class="big">🎉 Bravo!</div><div class="sub">Vse besede znaš. Odkljukaj “Le neznane”, da ponoviš ali ponastavi napredek.</div></div>';
        backEl.innerHTML=frontEl.innerHTML;
        return;
      }
      if(pos>=view.length) pos=view.length-1;
      var item=DECK[view[pos]];
      var frontSL = (dir==='sl2en');
      frontEl.innerHTML = frontSL ? faceHTML(item.sl,true,'Slovensko 🇸🇮') : faceHTML(item.en,false,'English');
      backEl.innerHTML  = frontSL ? faceHTML(item.en,false,'English')      : faceHTML(item.sl,true,'Slovensko 🇸🇮');
      posEl.textContent=(pos+1)+' / '+view.length;
      fillEl.style.width=((pos+1)/view.length*100)+'%';
      wrap.querySelectorAll('.fcq-audio').forEach(function(b){
        b.addEventListener('click',function(ev){ ev.stopPropagation(); speakSL(b.getAttribute('data-sl')); });
      });
    }

    function flip(){ flipped=!flipped; cardEl.classList.toggle('flipped',flipped); }
    function go(d){ if(!view.length) return; pos=(pos+d+view.length)%view.length; render(); }
    function mark(isKnown){
      if(!view.length) return;
      var id=idOf(view[pos]); known[id]=isKnown; saveKnown();
      if(onlyLearning && isKnown){ buildView(false); render(); }
      else { go(1); }
      knownEl.textContent='✅ '+knownCount()+' / '+DECK.length;
    }

    cardEl.addEventListener('click',flip);
    wrap.querySelector('.fcq-prev').addEventListener('click',function(){go(-1);});
    wrap.querySelector('.fcq-next').addEventListener('click',function(){go(1);});
    wrap.querySelector('.fcq-learning').addEventListener('click',function(){mark(false);});
    wrap.querySelector('.fcq-known-btn').addEventListener('click',function(){mark(true);});
    wrap.querySelector('.fcq-shuffle').addEventListener('click',function(){buildView(true);render();});
    dirBtn.addEventListener('click',function(){
      dir = (dir==='sl2en')?'en2sl':'sl2en';
      dirBtn.textContent = (dir==='sl2en')?'↔ SL → EN':'↔ EN → SL';
      render();
    });
    wrap.querySelector('.fcq-filter').addEventListener('change',function(e){
      onlyLearning=e.target.checked; buildView(false); render();
    });
    wrap.querySelector('.fcq-reset').addEventListener('click',function(){
      known={}; saveKnown(); buildView(false); render();
    });
    document.addEventListener('keydown',function(e){
      var fcSec=wrap.querySelector('#fcq-flashcards');
      if(fcSec.classList.contains('fcq-collapsed')) return;
      var tag=(e.target.tagName||'').toLowerCase();
      if(tag==='input'||tag==='textarea'||tag==='select') return;
      if(e.key==='ArrowRight'){ go(1); }
      else if(e.key==='ArrowLeft'){ go(-1); }
      else if(e.key===' '){ e.preventDefault(); flip(); }
    });

    buildView(true); render();

    /* ================= VOCAB QUIZ ================= */
    var qList=wrap.querySelector('#fcq-quiz-list');
    var qResult=wrap.querySelector('#fcq-quiz-result');
    var qSubmit=wrap.querySelector('#fcq-quiz-submit');
    var QN=Math.min(15, DECK.length);
    wrap.querySelector('#fcq-qn').textContent=QN;
    var quiz=[], answers=[];

    function makeQuiz(){
      var pool=DECK.slice(); shuf(pool); quiz=[]; answers=[];
      for(var i=0;i<QN;i++){
        var item=pool[i], sl2en=Math.random()<0.5;
        var prompt=sl2en?item.sl:item.en, correct=sl2en?item.en:item.sl;
        var opts=[correct], guard=0;
        while(opts.length<4 && guard<800){
          guard++;
          var c=DECK[Math.floor(Math.random()*DECK.length)];
          var v=sl2en?c.en:c.sl;
          if(opts.indexOf(v)===-1) opts.push(v);
        }
        shuf(opts);
        quiz.push({prompt:prompt,correct:correct,opts:opts,sl2en:sl2en,sl:item.sl});
        answers.push(null);
      }
    }

    function renderQuiz(){
      qResult.style.display='none'; qResult.innerHTML=''; qSubmit.style.display='';
      var h='';
      quiz.forEach(function(q,i){
        var audio = q.sl2en ? ' <button class="fcq-q-mini" data-sl="'+q.sl.replace(/"/g,'&quot;')+'">🔊</button>' : '';
        h+='<div class="fcq-q" data-i="'+i+'"><div class="fcq-q-prompt"><span class="fcq-q-num">'+(i+1)+'.</span> '
          + q.prompt + audio + '</div><div class="fcq-opts">';
        q.opts.forEach(function(opt,j){
          h+='<div class="fcq-opt" data-i="'+i+'" data-j="'+j+'">'+opt+'</div>';
        });
        h+='</div></div>';
      });
      qList.innerHTML=h;
      qList.querySelectorAll('.fcq-q-mini').forEach(function(b){
        b.addEventListener('click',function(){ speakSL(b.getAttribute('data-sl')); });
      });
      qList.querySelectorAll('.fcq-opt').forEach(function(o){
        o.addEventListener('click',function(){
          var i=+o.getAttribute('data-i'), j=+o.getAttribute('data-j');
          answers[i]=j;
          o.parentElement.querySelectorAll('.fcq-opt').forEach(function(x){x.classList.remove('sel');});
          o.classList.add('sel');
        });
      });
    }

    qSubmit.addEventListener('click',function(){
      var correct=0;
      quiz.forEach(function(q,i){
        var qEl=qList.querySelector('.fcq-q[data-i="'+i+'"]');
        var opts=qEl.querySelectorAll('.fcq-opt');
        opts.forEach(function(o){
          o.style.pointerEvents='none';
          var j=+o.getAttribute('data-j');
          if(q.opts[j]===q.correct) o.classList.add('ok');
          else if(answers[i]===j) o.classList.add('bad');
        });
        if(answers[i]!==null && q.opts[answers[i]]===q.correct) correct++;
      });
      var pct=Math.round(correct/quiz.length*100);
      var grade = pct>=90?'Odlično! 🎉 Besedišče obvladaš!'
        : pct>=75?'Prav dobro! 👏 Še malo vaje.'
        : pct>=50?'Dobro. 💪 Ponovi kartice in poskusi znova.'
        : 'Brez skrbi 🌱 — preglej kartice in poskusi spet!';
      qSubmit.style.display='none';
      qResult.style.display='block';
      qResult.innerHTML='<div class="big">'+correct+' / '+quiz.length+'</div>'
        +'<div class="pct">'+pct+'%</div><div class="grade">'+grade+'</div>';
      qResult.scrollIntoView({behavior:'smooth',block:'center'});
    });

    wrap.querySelector('.fcq-new-quiz').addEventListener('click',function(){
      makeQuiz(); renderQuiz(); wrap.querySelector('#fcq-quiz').scrollIntoView({behavior:'smooth',block:'start'});
    });

    makeQuiz(); renderQuiz();
  });
})();
</script>
"""

def inject(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    if MARKER in html:
        print('skip (already injected):', path)
        return
    idx = html.rfind('</body>')
    if idx == -1:
        print('NO </body>:', path)
        return
    html = html[:idx] + SNIPPET + '\n' + html[idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('injected:', path)

if __name__ == '__main__':
    for p in sys.argv[1:]:
        inject(p)
