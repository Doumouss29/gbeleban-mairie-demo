(function(){
  const input=document.getElementById('address-search-input');
  const button=document.getElementById('address-search-button');
  const resultsBox=document.getElementById('address-search-results');
  const destinationCard=document.getElementById('address-destination-card');
  const destinationLabel=document.getElementById('address-destination-label');
  const destinationSource=document.getElementById('address-destination-source');
  const routeButton=document.getElementById('address-route-button');
  if(!input||!button||!resultsBox||typeof map==='undefined') return;

  let searchMarker=null;
  let searchTimer=null;
  let activeRequest=0;

  function escapeHtml(value){
    return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  }

  function clearResults(){
    resultsBox.innerHTML='';
    resultsBox.classList.remove('open');
  }

  function showStatus(text){
    resultsBox.innerHTML=`<div class="websig-address-status">${escapeHtml(text)}</div>`;
    resultsBox.classList.add('open');
  }

  function sourceLabel(item){
    return item.source==='gbeleban'?'Adressage Gbéléban':'Google Maps';
  }

  function sourceIcon(item){
    return item.source==='gbeleban'?'📍':'G';
  }

  function selectResult(item){
    const lng=Number(item.longitude),lat=Number(item.latitude);
    if(!Number.isFinite(lng)||!Number.isFinite(lat)) return;

    if(searchMarker) searchMarker.remove();
    const el=document.createElement('div');
    el.className='websig-search-marker';
    searchMarker=new maplibregl.Marker({element:el,anchor:'bottom'}).setLngLat([lng,lat]).addTo(map);

    map.flyTo({center:[lng,lat],zoom:18,pitch:0,bearing:0,essential:true});

    const details=[];
    if(item.code) details.push(item.code);
    if(item.ilot) details.push(`Îlot ${item.ilot}`);
    if(item.lot) details.push(`Lot ${item.lot}`);
    const detailText=details.length?`<br><small>${details.map(escapeHtml).join(' · ')}</small>`:'';
    new maplibregl.Popup({offset:30,maxWidth:'360px'})
      .setLngLat([lng,lat])
      .setHTML(`<div class="websig-popup"><strong>${escapeHtml(item.label)}</strong><div>${escapeHtml(sourceLabel(item))}${detailText}</div></div>`)
      .addTo(map);

    if(destinationLabel) destinationLabel.textContent=item.label;
    if(destinationSource) destinationSource.textContent=sourceLabel(item);
    if(routeButton) routeButton.href=`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lat+','+lng)}`;
    if(destinationCard) destinationCard.classList.add('open');
    input.value=item.label;
    clearResults();
  }

  function renderResults(data){
    const items=Array.isArray(data.results)?data.results:[];
    if(!items.length){
      const suffix=data.google_enabled===false?' Recherche Google non activée sur le serveur.':'';
      showStatus(`Aucune adresse trouvée.${suffix}`);
      return;
    }
    resultsBox.innerHTML=items.map((item,index)=>{
      const detail=item.source==='gbeleban'
        ? [item.code,item.ilot?`Îlot ${item.ilot}`:'',item.lot?`Lot ${item.lot}`:''].filter(Boolean).join(' · ')
        : 'Résultat Google Maps';
      return `<div class="websig-address-item" data-result-index="${index}" role="button" tabindex="0"><span class="websig-address-source">${escapeHtml(sourceIcon(item))}</span><span><b>${escapeHtml(item.label)}</b><small>${escapeHtml(detail)}</small></span><span class="websig-address-badge ${item.source==='google'?'google':''}">${escapeHtml(sourceLabel(item))}</span></div>`;
    }).join('');
    resultsBox.classList.add('open');
    resultsBox.querySelectorAll('.websig-address-item').forEach(el=>{
      const choose=()=>selectResult(items[Number(el.dataset.resultIndex)]);
      el.addEventListener('click',choose);
      el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});
    });
  }

  async function runSearch(){
    const q=input.value.trim();
    if(q.length<2){clearResults();return;}
    const requestId=++activeRequest;
    showStatus('Recherche en cours...');
    try{
      const response=await fetch(`/api/recherche-adresse/?q=${encodeURIComponent(q)}`,{headers:{'Accept':'application/json'}});
      if(!response.ok) throw new Error('HTTP '+response.status);
      const data=await response.json();
      if(requestId!==activeRequest) return;
      renderResults(data);
    }catch(err){
      if(requestId!==activeRequest) return;
      showStatus('La recherche est temporairement indisponible.');
    }
  }

  button.addEventListener('click',runSearch);
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();runSearch();}});
  input.addEventListener('input',()=>{
    clearTimeout(searchTimer);
    if(input.value.trim().length<3){clearResults();return;}
    searchTimer=setTimeout(runSearch,350);
  });
  document.addEventListener('click',e=>{
    if(!resultsBox.contains(e.target)&&e.target!==input&&e.target!==button) clearResults();
  });
})();
