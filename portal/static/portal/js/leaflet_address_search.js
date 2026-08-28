(function(){
  function esc(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function sourceLabel(item){return item.source==='gbeleban'?'Adressage Gbéléban':'OpenStreetMap';}

  function attach(map, options={}){
    if(!map || typeof L==='undefined') return null;
    const position=options.position||'topleft';
    const placeholder=options.placeholder||'Rechercher une adresse…';
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
          if(!items.length){status('Aucune adresse trouvée.');return;}
          results.innerHTML=items.map((item,i)=>`<button type="button" class="gbl-leaflet-search-item" data-i="${i}"><span class="gbl-leaflet-search-pin">${item.source==='gbeleban'?'📍':'⌖'}</span><span><b>${esc(item.label)}</b><small>${esc(sourceLabel(item))}${item.code?' · '+esc(item.code):''}${item.ilot?' · Îlot '+esc(item.ilot):''}${item.lot?' · Lot '+esc(item.lot):''}</small></span></button>`).join('');
          results.classList.add('open');
          results.querySelectorAll('.gbl-leaflet-search-item').forEach(btn=>btn.addEventListener('click',()=>pick(items[Number(btn.dataset.i)])));
        }
        async function search(external){
          const q=input.value.trim();if(q.length<2){closeResults();return;}
          const requestId=++activeRequest;status('Recherche…');
          try{
            const response=await fetch(`/api/recherche-adresse/?q=${encodeURIComponent(q)}&external=${external?'1':'0'}`,{headers:{Accept:'application/json'}});
            if(!response.ok) throw new Error(String(response.status));
            const data=await response.json();if(requestId!==activeRequest)return;render(data);
          }catch(e){if(requestId===activeRequest)status('Recherche temporairement indisponible.');}
        }
        input.addEventListener('input',()=>{
          clearTimeout(timer);destination.classList.remove('open');
          const q=input.value.trim();if(q.length<2){closeResults();return;}
          timer=setTimeout(()=>search(false),220);
        });
        input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();clearTimeout(timer);search(true);}});
        clearBtn.addEventListener('click',()=>{input.value='';destination.classList.remove('open');closeResults();if(marker){map.removeLayer(marker);marker=null;}input.focus();});
        input.addEventListener('blur',()=>{clearTimeout(timer);if(input.value.trim().length>=2)timer=setTimeout(()=>search(true),320);});
        return wrap;
      }
    });
    const control=new SearchControl();control.addTo(map);return control;
  }
  window.GbelebanAddressSearch={attachLeaflet:attach};
})();
