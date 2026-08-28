(function(){
  const overlay=document.getElementById('address-search-overlay');
  const input=document.getElementById('address-search-input');
  const toggleButton=document.getElementById('address-search-toggle');
  const clearButton=document.getElementById('address-search-clear');
  const resultsBox=document.getElementById('address-search-results');
  const destinationCard=document.getElementById('address-destination-card');
  const destinationLabel=document.getElementById('address-destination-label');
  const destinationSource=document.getElementById('address-destination-source');
  const routeButton=document.getElementById('address-route-button');
  if(!overlay||!input||!resultsBox||typeof map==='undefined') return;
  const mapWrap=document.querySelector('.websig-map-wrap');
  if(mapWrap && overlay.parentElement!==mapWrap) mapWrap.appendChild(overlay);

  let searchMarker=null;
  let activeRequest=0;
  let timer=null;
  const isMobile=()=>window.matchMedia('(max-width:700px)').matches;

  function escapeHtml(value){return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
  function clearResults(){resultsBox.innerHTML='';resultsBox.classList.remove('open');}
  function showStatus(text){resultsBox.innerHTML=`<div class="websig-address-status">${escapeHtml(text)}</div>`;resultsBox.classList.add('open');}
  function sourceLabel(item){return item.source==='gbeleban'?'Adressage Gbéléban':'OpenStreetMap';}
  function sourceIcon(item){return item.source==='gbeleban'?'📍':'⌖';}
  function setCollapsed(value){overlay.classList.toggle('mobile-collapsed',!!value&&isMobile());}
  if(isMobile()) setCollapsed(true);
  if(toggleButton) toggleButton.addEventListener('click',()=>{if(isMobile()&&overlay.classList.contains('mobile-collapsed')){setCollapsed(false);setTimeout(()=>input.focus(),20);}else input.focus();});
  window.addEventListener('resize',()=>{if(isMobile()&&!input.value.trim())setCollapsed(true);else overlay.classList.remove('mobile-collapsed');});

  function selectResult(item){
    const lng=Number(item.longitude),lat=Number(item.latitude);if(!Number.isFinite(lng)||!Number.isFinite(lat)) return;
    if(searchMarker) searchMarker.remove();
    const el=document.createElement('div');el.className='websig-search-marker';
    searchMarker=new maplibregl.Marker({element:el,anchor:'bottom'}).setLngLat([lng,lat]).addTo(map);
    map.flyTo({center:[lng,lat],zoom:18,pitch:0,bearing:0,essential:true});
    const details=[];if(item.code)details.push(item.code);if(item.ilot)details.push(`Îlot ${item.ilot}`);if(item.lot)details.push(`Lot ${item.lot}`);
    const detailText=details.length?`<br><small>${details.map(escapeHtml).join(' · ')}</small>`:'';
    const routeUrl=`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lat+','+lng)}`;
    new maplibregl.Popup({offset:26,maxWidth:'280px',closeButton:true,closeOnClick:true})
      .setLngLat([lng,lat])
      .setHTML(`<div class="websig-popup"><strong>${escapeHtml(item.label)}</strong><div>${escapeHtml(sourceLabel(item))}${detailText}</div><a href="${routeUrl}" target="_blank" rel="noopener" title="Partir à cette adresse" aria-label="Partir à cette adresse" style="display:grid;width:32px;height:32px;place-items:center;margin-top:8px;background:#056b3c;color:#fff;border-radius:8px;text-decoration:none;font-weight:900;font-size:16px">➜</a></div>`)
      .addTo(map);
    if(destinationLabel)destinationLabel.textContent=item.label;
    if(destinationSource)destinationSource.textContent=sourceLabel(item);
    if(routeButton)routeButton.href=routeUrl;
    if(destinationCard)destinationCard.classList.add('open');
    input.value=item.label;clearResults();
  }

  function renderResults(data){
    const items=Array.isArray(data.results)?data.results:[];
    if(!items.length){showStatus(data.osm_message||'Aucune adresse trouvée.');return;}
    resultsBox.innerHTML=items.map((item,index)=>{
      const detail=item.source==='gbeleban'?[item.code,item.ilot?`Îlot ${item.ilot}`:'',item.lot?`Lot ${item.lot}`:''].filter(Boolean).join(' · '):'Résultat OpenStreetMap';
      return `<div class="websig-address-item" data-result-index="${index}" role="button" tabindex="0"><span class="websig-address-source">${escapeHtml(sourceIcon(item))}</span><span><b>${escapeHtml(item.label)}</b><small>${escapeHtml(detail)}</small></span><span class="websig-address-badge ${item.source==='osm'?'osm':''}">${escapeHtml(sourceLabel(item))}</span></div>`;
    }).join('');
    resultsBox.classList.add('open');
    resultsBox.querySelectorAll('.websig-address-item').forEach(el=>{const choose=()=>selectResult(items[Number(el.dataset.resultIndex)]);el.addEventListener('click',choose);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});});
  }

  async function runSearch(){
    const q=input.value.trim();if(q.length<2){clearResults();return;}
    const requestId=++activeRequest;showStatus('Recherche…');
    try{
      const response=await fetch(`/api/recherche-adresse/?q=${encodeURIComponent(q)}&external=1`,{headers:{Accept:'application/json'}});
      if(!response.ok)throw new Error('HTTP '+response.status);
      const data=await response.json();if(requestId!==activeRequest)return;renderResults(data);
    }catch(err){if(requestId===activeRequest)showStatus('La recherche est temporairement indisponible.');}
  }

  input.addEventListener('input',()=>{clearTimeout(timer);if(destinationCard)destinationCard.classList.remove('open');const q=input.value.trim();if(q.length<2){clearResults();return;}timer=setTimeout(runSearch,700);});
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();clearTimeout(timer);runSearch();}});
  if(clearButton)clearButton.addEventListener('click',()=>{clearTimeout(timer);activeRequest++;input.value='';if(destinationCard)destinationCard.classList.remove('open');clearResults();if(searchMarker){searchMarker.remove();searchMarker=null;}if(isMobile())setCollapsed(true);else input.focus();});
  document.addEventListener('click',e=>{if(!resultsBox.contains(e.target)&&e.target!==input&&e.target!==clearButton&&e.target!==toggleButton)clearResults();});
})();
