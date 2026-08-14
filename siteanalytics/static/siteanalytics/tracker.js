(function(){
  function isPrivatePath(path){
    return ['/admin/','/gestion/','/connexion/','/deconnexion/','/mon-espace/','/urbanisme/','/dashboard/','/collecte-municipale/','/pilotage-projets/','/analytics/','/api/','/static/'].some(function(prefix){return path.indexOf(prefix)===0;});
  }
  document.addEventListener('click', function(event){
    var link = event.target.closest && event.target.closest('a[href]');
    if(!link) return;
    try{
      var url = new URL(link.href, window.location.href);
      if(url.origin !== window.location.origin || isPrivatePath(url.pathname)) return;
      var payload = JSON.stringify({
        source: window.location.pathname,
        target: url.pathname,
        label: (link.innerText || link.getAttribute('aria-label') || '').trim().replace(/\s+/g,' ').slice(0,220)
      });
      if(navigator.sendBeacon){
        navigator.sendBeacon('/analytics/track-click/', new Blob([payload], {type:'application/json'}));
      }else{
        fetch('/analytics/track-click/', {method:'POST',headers:{'Content-Type':'application/json'},body:payload,keepalive:true,credentials:'same-origin'}).catch(function(){});
      }
    }catch(e){}
  }, true);
})();
