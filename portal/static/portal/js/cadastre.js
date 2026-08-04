const cmap=L.map('cadastre-map').setView([9.5846,-8.1318],16);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:21,attribution:'© OpenStreetMap'}).addTo(cmap);
let parcelLayer=null;
function parcelPopup(p){return `<div><b>Référence</b> : ${p.reference||''}</div><div><b>Section</b> : ${p.section||''}</div><div><b>Îlot</b> : ${p.ilot||''}</div><div><b>Lot</b> : ${p.lot||''}</div><div><b>Parcelle</b> : ${p.parcelle||''}</div><div><b>Superficie</b> : ${p.superficie??''} m²</div><div><b>Usage</b> : ${p.usage||''}</div>`}
fetch('/api/cadastre.geojson').then(r=>r.json()).then(data=>{
  parcelLayer=L.geoJSON(data,{style:{color:'#ef7d00',weight:2,fillOpacity:.18},onEachFeature:(f,l)=>l.bindPopup(parcelPopup(f.properties||{}))}).addTo(cmap);
  if(parcelLayer.getLayers().length){cmap.fitBounds(parcelLayer.getBounds(),{padding:[20,20]});}
});
const form=document.getElementById('parcel-search');
const results=document.getElementById('search-results');
form.addEventListener('submit',async e=>{
  e.preventDefault();
  const params=new URLSearchParams(new FormData(form));
  const data=await fetch('/api/cadastre/recherche/?'+params.toString()).then(r=>r.json());
  results.innerHTML='';
  if(!data.results.length){results.innerHTML='<p>Aucune parcelle trouvée.</p>';return;}
  data.results.forEach(r=>{
    const b=document.createElement('button');
    b.type='button';b.className='parcel-result';b.textContent=`${r.reference} — S:${r.section||'-'} I:${r.ilot||'-'} L:${r.lot||'-'} P:${r.parcelle||'-'}`;
    b.onclick=()=>{
      if(!parcelLayer)return;
      const target=parcelLayer.getLayers().find(l=>String(l.feature?.properties?.id)===String(r.id));
      if(target){if(target.getBounds)cmap.fitBounds(target.getBounds(),{padding:[80,80],maxZoom:19});else cmap.setView(target.getLatLng(),19);target.openPopup();}
    };
    results.appendChild(b);
  });
});
