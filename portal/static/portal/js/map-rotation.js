(function(){
  function initRotation360(){
    if(typeof map==='undefined') return;
    try{
      if(map.dragRotate) map.dragRotate.enable();
      if(map.touchZoomRotate){
        map.touchZoomRotate.enable();
        if(map.touchZoomRotate.enableRotation) map.touchZoomRotate.enableRotation();
      }
    }catch(e){}

    const wrap=document.querySelector('.websig-map-wrap');
    if(!wrap || document.getElementById('websig-rotate-360')) return;

    const control=document.createElement('div');
    control.id='websig-rotate-360';
    control.style.cssText='position:absolute;z-index:14;right:10px;top:155px;display:none;flex-direction:column;gap:4px;background:#fff;border:1px solid #d9ded9;border-radius:10px;padding:5px;box-shadow:0 5px 18px #0002';

    function button(text,label,delta){
      const btn=document.createElement('button');
      btn.type='button';
      btn.textContent=text;
      btn.title=label;
      btn.setAttribute('aria-label',label);
      btn.style.cssText='width:40px;height:40px;border:0;border-radius:8px;background:#fff;color:#173d2f;font-size:23px;font-weight:900;cursor:pointer;touch-action:manipulation';
      btn.addEventListener('click',function(e){
        e.preventDefault();
        e.stopPropagation();
        map.easeTo({bearing:map.getBearing()+delta,duration:250});
      });
      return btn;
    }

    control.appendChild(button('↺','Tourner de 30° vers la gauche',-30));
    control.appendChild(button('↻','Tourner de 30° vers la droite',30));
    wrap.appendChild(control);

    function sync(){
      let enabled=false;
      try{enabled=(typeof is3D!=='undefined' && is3D);}catch(e){}
      control.style.display=enabled?'flex':'none';
    }

    const toggle=document.getElementById('toggle-3d');
    if(toggle) toggle.addEventListener('click',function(){setTimeout(sync,80);});
    sync();
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',initRotation360);
  else initRotation360();
})();
