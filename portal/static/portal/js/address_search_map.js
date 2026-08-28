(function(){
  const overlay=document.getElementById('address-search-overlay');
  const input=document.getElementById('address-search-input');
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

  function escapeHtml(value){return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
  function clearResults(){resultsBox.innerHTML='';resultsBox.classList.remove('open');}
  function showStatus(text){resultsBox.innerHTML=`<div class="websig-address-status">${escapeHtml(text)}</div>`;resultsBox.classList.add('open');}
  function sourceLabel(item){return item.source==='gbeleban'?'Adressage Gbéléban':'OpenStreetMap';}
  function sourceIcon(item){return item.source==='gbeleban'?'📍':'⌖';}

  function selectResult(item){
    const lng=Number(item.longitude),lat=Number(item.latitude);if(!Number.isFinite(lng)||!Number.isFinite(lat)) return;
    if(searchMarker) searchMarker.remove();
    const el=document.createElement('div');el.className='websig-search-marker';
    searchMarker=new maplibregl.Marker({element:el,anchor:'bottom'}).setLngLat([lng,lat]).addTo(map);
    map.flyTo({center:[lng,lat],zoom:18,pitch:0,bearing:0,essential:true});
    const details=[];if(item.code)details.push(item.code);if(item.ilot)details.push(`Îlot ${item.ilot}`);if(item.lot)details.push(`Lot ${item.lot}`);
    const detailText=details.length?`<br><small>${details.map(escapeHtml).join(' · ')}</small>`:'';
    new maplibregl.Popup({offset:30,maxWidth:'360px'}).setLngLat([lng,lat]).setHTML(`<div class="websig-popup"><strong>${escapeHtml(item.label)}</strong><div>${escapeHtml(sourceLabel(item))}${detailText}</div><a href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lat+','+lng)}" target="_blank" rel="noopener" style="display:inline-block;margin-top:8px;font-weight:800;color:#056b3c">Partir à cette adresse</a></div>`).addTo(map);
    if(destinationLabel)destinationLabel.textContent=item.label;if(destinationSource)destinationSource.textContent=sourceLabel(item);if(routeButton)routeButton.href=`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lat+','+lng)}`;if(destinationCard)destinationCard.classList.add('open');
    input.value=item.label;clearResults();
  }

  function renderResults(data){
    const items=Array.isArray(data.results)?data.results:[];if(!items.length){showStatus('Aucune adresse trouvée.');return;}
    resultsBox.innerHTML=items.map((item,index)=>{const detail=item.source==='gbeleban'?[item.code,item.ilot?`Îlot ${item.ilot}`:'',item.lot?`Lot ${item.lot}`:''].filter(Boolean).join(' · '):'Résultat OpenStreetMap';return `<div class="websig-address-item" data-result-index="${index}" role="button" tabindex="0"><span class="websig-address-source">${escapeHtml(sourceIcon(item))}</span><span><b>${escapeHtml(item.label)}</b><small>${escapeHtml(detail)}</small></span><span class="websig-address-badge ${item.source==='osm'?'osm':''}">${escapeHtml(sourceLabel(item))}</span></div>`;}).join('');
    resultsBox.classList.add('open');
    resultsBox.querySelectorAll('.websig-address-item').forEach(el=>{const choose=()=>selectResult(items[Number(el.dataset.resultIndex)]);el.addEventListener('click',choose);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});});
  }

  async function runSearch(external){
    const q=input.value.trim();if(q.length<2){clearResults();return;}
    const requestId=++activeRequest;showStatus('Recherche…');
    try{const response=await fetch(`/api/recherche-adresse/?q=${encodeURIComponent(q)}&external=${external?'1':'0'}`,{headers:{Accept:'application/json'}});if(!response.ok)throw new Error('HTTP '+response.status);const data=await response.json();if(requestId!==activeRequest)return;renderResults(data);}catch(err){if(requestId===activeRequest)showStatus('La recherche est temporairement indisponible.');}
  }

  input.addEventListener('input',()=>{clearTimeout(timer);if(destinationCard)destinationCard.classList.remove('open');const q=input.value.trim();if(q.length<2){clearResults();return;}timer=setTimeout(()=>runSearch(false),180);});
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();clearTimeout(timer);runSearch(true);}});
  input.addEventListener('blur',()=>{clearTimeout(timer);if(input.value.trim().length>=2)timer=setTimeout(()=>runSearch(true),280);});
  if(clearButton)clearButton.addEventListener('click',()=>{input.value='';if(destinationCard)destinationCard.classList.remove('open');clearResults();if(searchMarker){searchMarker.remove();searchMarker=null;}input.focus();});
  document.addEventListener('click',e=>{if(!resultsBox.contains(e.target)&&e.target!==input&&e.target!==clearButton)clearResults();});
})();
