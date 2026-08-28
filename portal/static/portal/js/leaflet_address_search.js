(function(){
  if(!document.getElementById('gbl-leaflet-search-style')){
    const style=document.createElement('style');
    style.id='gbl-leaflet-search-style';
    style.textContent=`.gbl-leaflet-search{font-family:inherit}.gbl-leaflet-search-shell{display:grid;grid-template-columns:34px 1fr 30px;align-items:center;background:#fff;border:1px solid #d8ddd9;border-radius:10px;box-shadow:0 2px 10px #0002;overflow:hidden}.gbl-leaflet-search-toggle{border:0;background:#fff;color:#52625a;font-size:18px;cursor:pointer;height:38px;display:grid;place-items:center}.gbl-leaflet-search input{border:0!important;outline:0!important;box-shadow:none!important;background:#fff!important;padding:10px 4px!important;width:100%!important;font-size:13px!important}.gbl-leaflet-search-clear{border:0;background:#fff;color:#7b847f;font-size:19px;cursor:pointer;height:36px}.gbl-leaflet-search-results{display:none;margin-top:5px;background:#fff;border:1px solid #d8ddd9;border-radius:10px;box-shadow:0 7px 22px #0003;max-height:300px;overflow:auto}.gbl-leaflet-search-results.open{display:block}.gbl-leaflet-search-item{display:grid;grid-template-columns:26px 1fr;gap:7px;width:100%;border:0;border-bottom:1px solid #edf0ed;background:#fff;text-align:left;padding:8px;cursor:pointer}.gbl-leaflet-search-item:hover{background:#f7faf8}.gbl-leaflet-search-pin{display:grid;place-items:center}.gbl-leaflet-search-item b{display:block;color:#173d2f;font-size:12px}.gbl-leaflet-search-item small{display:block;color:#6f7873;font-size:10px;margin-top:2px}.gbl-leaflet-search-status{padding:9px 11px;font-size:11px;color:#68736d}.gbl-leaflet-destination{display:none;margin-top:5px;background:#fff;border:1px solid #d8ddd9;border-radius:10px;box-shadow:0 7px 22px #0003;padding:8px 9px;gap:8px;align-items:center;justify-content:space-between}.gbl-leaflet-destination.open{display:flex}.gbl-leaflet-destination strong{display:block;font-size:11px;color:#173d2f;max-width:215px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.gbl-leaflet-destination small{display:block;font-size:9px;color:#6f7873}.gbl-leaflet-route-icon{width:34px;height:34px;display:grid!important;place-items:center;flex:0 0 34px;text-decoration:none;background:#056b3c;color:#fff!important;border-radius:9px;font-weight:900;font-size:17px;line-height:1}.gbl-leaflet-search.collapsed{width:40px!important}.gbl-leaflet-search.collapsed .gbl-leaflet-search-shell{grid-template-columns:38px;border-radius:9px}.gbl-leaflet-search.collapsed input,.gbl-leaflet-search.collapsed .gbl-leaflet-search-clear,.gbl-leaflet-search.collapsed .gbl-leaflet-search-results,.gbl-leaflet-search.collapsed .gbl-leaflet-destination{display:none!important}@media(max-width:700px){.gbl-leaflet-search{width:min(290px,calc(100vw - 88px))!important}.gbl-leaflet-search.mobile-collapsed{width:40px!important}.gbl-leaflet-search.mobile-collapsed .gbl-leaflet-search-shell{grid-template-columns:38px;border-radius:9px}.gbl-leaflet-search.mobile-collapsed input,.gbl-leaflet-search.mobile-collapsed .gbl-leaflet-search-clear,.gbl-leaflet-search.mobile-collapsed .gbl-leaflet-search-results,.gbl-leaflet-search.mobile-collapsed .gbl-leaflet-destination{display:none!important}.gbl-leaflet-search-results{max-height:42vh}.gbl-leaflet-search-item b{font-size:11px}.gbl-leaflet-search-item small{font-size:9px}.leaflet-popup-content-wrapper{max-width:calc(100vw - 42px)}.leaflet-popup-content{margin:11px 14px!important;max-width:calc(100vw - 70px)!important;font-size:12px}.leaflet-popup-close-button{font-size:20px!important;width:28px!important;height:28px!important}}`;
    document.head.appendChild(style);
  }

  function esc(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function sourceLabel(item){return item.source==='gbeleban'?'Adressage Gbéléban':'OpenStreetMap';}

  function attach(map, options={}){
    if(!map || typeof L==='undefined') return null;
    const position=options.position||'topleft';
    const placeholder=options.placeholder||'Rechercher une adresse, un lieu ou une parcelle…';
    let marker=null;
    let timer=null;
    let activeRequest=0;

    const SearchControl=L.Control.extend({
      options:{position},
      onAdd:function(){
        const wrap=L.DomUtil.create('div','gbl-leaflet-search leaflet-bar');
        wrap.innerHTML=`<div class="gbl-leaflet-search-shell"><button type="button" class="gbl-leaflet-search-toggle" aria-label="Ouvrir la recherche">⌕</button><input type="search" autocomplete="off" placeholder="${esc(placeholder)}" aria-label="Rechercher une adresse"><button type="button" class="gbl-leaflet-search-clear" aria-label="Effacer">×</button></div><div class="gbl-leaflet-search-results"></div><div class="gbl-leaflet-destination"><div><strong></strong><small></small></div><a class="gbl-leaflet-route-icon" target="_blank" rel="noopener" title="Partir à cette adresse" aria-label="Partir à cette adresse">➜</a></div>`;
        Object.assign(wrap.style,{background:'transparent',border:'0',boxShadow:'none',width:options.width||'320px',maxWidth:'calc(100vw - 90px)'});
        const input=wrap.querySelector('input');
        const toggleBtn=wrap.querySelector('.gbl-leaflet-search-toggle');
        const clearBtn=wrap.querySelector('.gbl-leaflet-search-clear');
        const results=wrap.querySelector('.gbl-leaflet-search-results');
        const destination=wrap.querySelector('.gbl-leaflet-destination');
        const destLabel=destination.querySelector('strong');
        const destSource=destination.querySelector('small');
        const route=destination.querySelector('a');

        L.DomEvent.disableClickPropagation(wrap);L.DomEvent.disableScrollPropagation(wrap);

        const isMobile=()=>window.matchMedia('(max-width:700px)').matches;
        function setMobileCollapsed(value){
          wrap.classList.toggle('mobile-collapsed',!!value&&isMobile());
          toggleBtn.setAttribute('aria-label',value?'Ouvrir la recherche':'Recherche');
        }
        if(isMobile()) setMobileCollapsed(true);
        toggleBtn.addEventListener('click',()=>{
          if(isMobile() && wrap.classList.contains('mobile-collapsed')){
            setMobileCollapsed(false);setTimeout(()=>input.focus(),20);
          }else input.focus();
        });
        window.addEventListener('resize',()=>{if(isMobile()&&!input.value.trim())setMobileCollapsed(true);else wrap.classList.remove('mobile-collapsed');});

        function closeResults(){results.innerHTML='';results.classList.remove('open');}
        function status(text){results.innerHTML=`<div class="gbl-leaflet-search-status">${esc(text)}</div>`;results.classList.add('open');}
        function pick(item){
          const lat=Number(item.latitude),lng=Number(item.longitude);if(!Number.isFinite(lat)||!Number.isFinite(lng)) return;
          if(marker) map.removeLayer(marker);
          marker=L.marker([lat,lng],{zIndexOffset:1500}).addTo(map);
          const routeUrl=`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lat+','+lng)}`;
          marker.bindPopup(`<div style="min-width:170px;max-width:240px"><strong>${esc(item.label)}</strong><br><small>${esc(sourceLabel(item))}${item.code?' · '+esc(item.code):''}</small><br><a href="${routeUrl}" target="_blank" rel="noopener" title="Partir à cette adresse" aria-label="Partir à cette adresse" style="display:grid;width:32px;height:32px;place-items:center;margin-top:8px;background:#056b3c;color:#fff;border-radius:8px;text-decoration:none;font-weight:900;font-size:16px">➜</a></div>`,{maxWidth:260}).openPopup();
          map.flyTo([lat,lng],Math.max(map.getZoom(),18),{animate:true});
          input.value=item.label;
          destLabel.textContent=item.label;destSource.textContent=sourceLabel(item);route.href=routeUrl;destination.classList.add('open');
          closeResults();
          if(typeof options.onSelect==='function') options.onSelect(item,marker);
        }
        function render(data){
          const items=Array.isArray(data.results)?data.results:[];
          if(!items.length){status(data.osm_message||'Aucune adresse trouvée.');return;}
          results.innerHTML=items.map((item,i)=>`<button type="button" class="gbl-leaflet-search-item" data-i="${i}"><span class="gbl-leaflet-search-pin">${item.source==='gbeleban'?'📍':'⌖'}</span><span><b>${esc(item.label)}</b><small>${esc(sourceLabel(item))}${item.code?' · '+esc(item.code):''}${item.ilot?' · Îlot '+esc(item.ilot):''}${item.lot?' · Lot '+esc(item.lot):''}</small></span></button>`).join('');
          results.classList.add('open');
          results.querySelectorAll('.gbl-leaflet-search-item').forEach(btn=>btn.addEventListener('click',()=>pick(items[Number(btn.dataset.i)])));
        }
        async function search(){
          const q=input.value.trim();if(q.length<2){closeResults();return;}
          const requestId=++activeRequest;status('Recherche…');
          try{
            const response=await fetch(`/api/recherche-adresse/?q=${encodeURIComponent(q)}&external=1&all=${options.includeUnpublished?'1':'0'}`,{headers:{Accept:'application/json'}});
            if(!response.ok) throw new Error(String(response.status));
            const data=await response.json();if(requestId!==activeRequest)return;render(data);
          }catch(e){if(requestId===activeRequest)status('Recherche temporairement indisponible.');}
        }
        input.addEventListener('input',()=>{
          clearTimeout(timer);destination.classList.remove('open');
          const q=input.value.trim();if(q.length<2){closeResults();return;}
          timer=setTimeout(search,700);
        });
        input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();clearTimeout(timer);search();}});
        clearBtn.addEventListener('click',()=>{clearTimeout(timer);activeRequest++;input.value='';destination.classList.remove('open');closeResults();if(marker){map.removeLayer(marker);marker=null;}if(isMobile())setMobileCollapsed(true);else input.focus();});
        return wrap;
      }
    });
    const control=new SearchControl();control.addTo(map);return control;
  }
  window.GbelebanAddressSearch={attachLeaflet:attach};
})();
