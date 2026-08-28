(function(){
  if(!document.getElementById('gbl-leaflet-search-style')){
    const style=document.createElement('style');
    style.id='gbl-leaflet-search-style';
    style.textContent=`.gbl-leaflet-search{font-family:inherit}.gbl-leaflet-search-shell{display:grid;grid-template-columns:28px 1fr 30px;align-items:center;background:#fff;border:1px solid #d8ddd9;border-radius:10px;box-shadow:0 2px 10px #0002;overflow:hidden}.gbl-leaflet-search-icon{display:grid;place-items:center;color:#52625a;font-size:18px}.gbl-leaflet-search input{border:0!important;outline:0!important;box-shadow:none!important;background:#fff!important;padding:10px 4px!important;width:100%!important;font-size:13px!important}.gbl-leaflet-search-clear{border:0;background:#fff;color:#7b847f;font-size:19px;cursor:pointer;height:36px}.gbl-leaflet-search-results{display:none;margin-top:5px;background:#fff;border:1px solid #d8ddd9;border-radius:10px;box-shadow:0 7px 22px #0003;max-height:340px;overflow:auto}.gbl-leaflet-search-results.open{display:block}.gbl-leaflet-search-item{display:grid;grid-template-columns:28px 1fr;gap:7px;width:100%;border:0;border-bottom:1px solid #edf0ed;background:#fff;text-align:left;padding:9px;cursor:pointer}.gbl-leaflet-search-item:hover{background:#f7faf8}.gbl-leaflet-search-pin{display:grid;place-items:center}.gbl-leaflet-search-item b{display:block;color:#173d2f;font-size:12px}.gbl-leaflet-search-item small{display:block;color:#6f7873;font-size:10px;margin-top:2px}.gbl-leaflet-search-status{padding:9px 11px;font-size:11px;color:#68736d}.gbl-leaflet-destination{display:none;margin-top:5px;background:#fff;border:1px solid #d8ddd9;border-radius:10px;box-shadow:0 7px 22px #0003;padding:9px 10px;gap:8px;align-items:center;justify-content:space-between}.gbl-leaflet-destination.open{display:flex}.gbl-leaflet-destination strong{display:block;font-size:11px;color:#173d2f;max-width:230px}.gbl-leaflet-destination small{display:block;font-size:9px;color:#6f7873}.gbl-leaflet-destination a{white-space:nowrap;text-decoration:none;background:#056b3c;color:#fff;border-radius:8px;padding:7px 9px;font-weight:800;font-size:10px}@media(max-width:700px){.gbl-leaflet-search{width:min(330px,calc(100vw - 82px))!important}.gbl-leaflet-destination{align-items:flex-start;flex-direction:column}.gbl-leaflet-destination a{width:100%;box-sizing:border-box;text-align:center}}`;
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
        wrap.innerHTML=`<div class="gbl-leaflet-search-shell"><span class="gbl-leaflet-search-icon">⌕</span><input type="search" autocomplete="off" placeholder="${esc(placeholder)}" aria-label="Rechercher une adresse"><button type="button" class="gbl-leaflet-search-clear" aria-label="Effacer">×</button></div><div class="gbl-leaflet-search-results"></div><div class="gbl-leaflet-destination"><div><strong></strong><small></small></div><a target="_blank" rel="noopener">Partir à cette adresse</a></div>`;
        Object.assign(wrap.style,{background:'transparent',border:'0',boxShadow:'none',width:options.width||'390px',maxWidth:'calc(100vw - 90px)'});
        const input=wrap.querySelector('input');
        const clearBtn=wrap.querySelector('.gbl-leaflet-search-clear');
        const results=wrap.querySelector('.gbl-leaflet-search-results');
        const destination=wrap.querySelector('.gbl-leaflet-destination');
        const destLabel=destination.querySelector('strong');
        const destSource=destination.querySelector('small');
        const route=destination.querySelector('a');

        L.DomEvent.disableClickPropagation(wrap);L.DomEvent.disableScrollPropagation(wrap);

        function closeResults(){results.innerHTML='';results.classList.remove('open');}
        function status(text){results.innerHTML=`<div class="gbl-leaflet-search-status">${esc(text)}</div>`;results.classList.add('open');}
        function pick(item){
          const lat=Number(item.latitude),lng=Number(item.longitude);if(!Number.isFinite(lat)||!Number.isFinite(lng)) return;
          if(marker) map.removeLayer(marker);
          marker=L.marker([lat,lng],{zIndexOffset:1500}).addTo(map);
          marker.bindPopup(`<div style="min-width:210px"><strong>${esc(item.label)}</strong><br><small>${esc(sourceLabel(item))}${item.code?' · '+esc(item.code):''}</small><br><a href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lat+','+lng)}" target="_blank" rel="noopener" style="display:inline-block;margin-top:8px;font-weight:800;color:#056b3c">Partir à cette adresse</a></div>`).openPopup();
          map.flyTo([lat,lng],Math.max(map.getZoom(),18),{animate:true});
          input.value=item.label;
          destLabel.textContent=item.label;destSource.textContent=sourceLabel(item);route.href=`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lat+','+lng)}`;destination.classList.add('open');
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
          // Un seul appel après une courte pause : résultats Gbéléban + OSM dans la même liste.
          timer=setTimeout(search,700);
        });
        input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();clearTimeout(timer);search();}});
        clearBtn.addEventListener('click',()=>{clearTimeout(timer);activeRequest++;input.value='';destination.classList.remove('open');closeResults();if(marker){map.removeLayer(marker);marker=null;}input.focus();});
        return wrap;
      }
    });
    const control=new SearchControl();control.addTo(map);return control;
  }
  window.GbelebanAddressSearch={attachLeaflet:attach};
})();
