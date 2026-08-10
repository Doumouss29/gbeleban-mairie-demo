const DEFAULT_CENTER=[-8.1260,9.5845];
const DEFAULT_ZOOM=14.2;
let is3D=false;
let publicData=null;
const markers=[];

const GROUPS={
  'ADMINISTRATION & SERVICES PUBLICS':{color:'#e67e22',icon:'🏛️',height:7},
  'ÉDUCATION':{color:'#2f6fb2',icon:'🎓',height:6},
  'SANTÉ & ACTION SOCIALE':{color:'#c7473c',icon:'🏥',height:8},
  'COMMERCES & TRANSPORTS':{color:'#b78334',icon:'🛒',height:5},
  'SPORTS & LOISIRS':{color:'#6f52a1',icon:'⚽',height:2.2},
  'ESPACES VERTS & ENVIRONNEMENT':{color:'#2f8a57',icon:'🌳',height:1.2},
  'CULTURE & LIEUX REMARQUABLES':{color:'#d3a321',icon:'⭐',height:4},
  'CULTES':{color:'#7a5a91',icon:'🕊️',height:6.5},
  'ÉQUIPEMENTS TECHNIQUES':{color:'#557789',icon:'⚙️',height:5.5},
  'CIMETIÈRE':{color:'#77756f',icon:'✦',height:1.4}
};

const map=new maplibregl.Map({
  container:'map',
  center:DEFAULT_CENTER,
  zoom:DEFAULT_ZOOM,
  pitch:0,
  bearing:0,
  attributionControl:true,
  style:{
    version:8,
    sources:{
      osm:{
        type:'raster',
        tiles:[
          'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
          'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
          'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
        ],
        tileSize:256,
        attribution:'© OpenStreetMap contributors'
      }
    },
    layers:[{id:'osm',type:'raster',source:'osm'}]
  }
});

map.addControl(new maplibregl.NavigationControl({visualizePitch:true}),'top-right');
map.addControl(new maplibregl.ScaleControl({maxWidth:120,unit:'metric'}));

function escapeHtml(value){
  return String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function popupHtml(props){
  const rows=[];
  if(props.AFFECTATION) rows.push(['Affectation',props.AFFECTATION]);
  if(props.GROUPE) rows.push(['Thématique',props.GROUPE]);
  if(props.ILOT) rows.push(['Îlot',props.ILOT]);
  if(props.LOT) rows.push(['Lot',props.LOT]);
  if(props.SUPERFICIE!==null && props.SUPERFICIE!==undefined && props.SUPERFICIE!==''){
    const n=Number(props.SUPERFICIE);
    rows.push(['Superficie',Number.isFinite(n)?`${n.toLocaleString('fr-FR')} m²`:props.SUPERFICIE]);
  }
  return `<div class="websig-popup"><strong>${escapeHtml(props.AFFECTATION||'Équipement')}</strong><dl>${rows.map(([k,v])=>`<dt>${escapeHtml(k)}</dt><dd>${escapeHtml(v)}</dd>`).join('')}</dl></div>`;
}

function ringArea(ring){
  let a=0;
  for(let i=0;i<ring.length-1;i++) a+=ring[i][0]*ring[i+1][1]-ring[i+1][0]*ring[i][1];
  return a/2;
}

function ringCentroid(ring){
  let area2=0,cx=0,cy=0;
  for(let i=0;i<ring.length-1;i++){
    const p=ring[i],q=ring[i+1];
    const cross=p[0]*q[1]-q[0]*p[1];
    area2+=cross;
    cx+=(p[0]+q[0])*cross;
    cy+=(p[1]+q[1])*cross;
  }
  if(Math.abs(area2)<1e-12){
    const pts=ring.slice(0,-1);
    return [pts.reduce((s,p)=>s+p[0],0)/pts.length,pts.reduce((s,p)=>s+p[1],0)/pts.length];
  }
  return [cx/(3*area2),cy/(3*area2)];
}

function featureCentroid(feature){
  const g=feature.geometry||{};
  if(g.type==='Point') return g.coordinates;
  let rings=[];
  if(g.type==='Polygon') rings=[g.coordinates[0]];
  if(g.type==='MultiPolygon') rings=g.coordinates.map(poly=>poly[0]);
  if(!rings.length) return DEFAULT_CENTER;
  rings.sort((a,b)=>Math.abs(ringArea(b))-Math.abs(ringArea(a)));
  return ringCentroid(rings[0]);
}

function selectedGroups(){
  return new Set([...document.querySelectorAll('.group-toggle:checked')].map(cb=>cb.dataset.group));
}

function layerId(group){
  return `websig-3d-${Object.keys(GROUPS).indexOf(group)}`;
}

function syncAllGroupsButton(){
  const btn=document.getElementById('toggle-all-groups');
  const boxes=[...document.querySelectorAll('.group-toggle')];
  if(!btn||!boxes.length) return;
  const allChecked=boxes.every(cb=>cb.checked);
  btn.textContent=allChecked?'Tout décocher':'Tout cocher';
  btn.setAttribute('aria-pressed',allChecked?'true':'false');
}

function updateVisibility(){
  const selected=selectedGroups();
  markers.forEach(item=>{
    item.element.style.display=(!is3D && selected.has(item.group))?'grid':'none';
  });
  Object.keys(GROUPS).forEach(group=>{
    const id=layerId(group);
    if(map.getLayer(id)){
      const visible=is3D && selected.has(group);
      map.setLayoutProperty(id,'visibility',visible?'visible':'none');
    }
  });
  syncAllGroupsButton();
}

function setupAllGroupsToggle(){
  const btn=document.getElementById('toggle-all-groups');
  const boxes=[...document.querySelectorAll('.group-toggle')];
  if(!btn||!boxes.length) return;
  btn.addEventListener('click',()=>{
    const shouldCheck=!boxes.every(cb=>cb.checked);
    boxes.forEach(cb=>{cb.checked=shouldCheck;});
    updateVisibility();
  });
  syncAllGroupsButton();
}

function setupSidebarResize(){
  const grid=document.querySelector('.websig-grid');
  const handle=document.getElementById('websig-resizer');
  if(!grid||!handle) return;

  const MIN_WIDTH=190;
  const MAX_WIDTH=520;
  const storageKey='gbeleban-websig-sidebar-width';

  function applyWidth(width,save=true){
    const w=Math.max(MIN_WIDTH,Math.min(MAX_WIDTH,Number(width)||230));
    grid.style.setProperty('--websig-side-width',`${w}px`);
    if(save){
      try{localStorage.setItem(storageKey,String(Math.round(w)));}catch(e){}
    }
    requestAnimationFrame(()=>map.resize());
  }

  try{
    const saved=parseFloat(localStorage.getItem(storageKey));
    if(Number.isFinite(saved)) applyWidth(saved,false);
  }catch(e){}

  function widthFromPointer(clientX){
    const rect=grid.getBoundingClientRect();
    applyWidth(clientX-rect.left);
  }

  handle.addEventListener('pointerdown',e=>{
    if(window.matchMedia('(max-width:1100px)').matches) return;
    handle.setPointerCapture(e.pointerId);
    handle.classList.add('active');
    document.body.classList.add('websig-resizing');
    e.preventDefault();
  });
  handle.addEventListener('pointermove',e=>{
    if(handle.hasPointerCapture(e.pointerId)) widthFromPointer(e.clientX);
  });
  function stopResize(e){
    if(e.pointerId!==undefined && handle.hasPointerCapture(e.pointerId)) handle.releasePointerCapture(e.pointerId);
    handle.classList.remove('active');
    document.body.classList.remove('websig-resizing');
    requestAnimationFrame(()=>map.resize());
  }
  handle.addEventListener('pointerup',stopResize);
  handle.addEventListener('pointercancel',stopResize);
  handle.addEventListener('keydown',e=>{
    if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight') return;
    const current=parseFloat(getComputedStyle(grid).getPropertyValue('--websig-side-width'))||230;
    applyWidth(current+(e.key==='ArrowRight'?20:-20));
    e.preventDefault();
  });
}

function sizeWebsigToViewport(){
  const grid=document.querySelector('.websig-grid');
  if(!grid) return;
  if(window.matchMedia('(max-width:1100px)').matches){
    grid.style.height='';
    requestAnimationFrame(()=>map.resize());
    return;
  }
  const top=grid.getBoundingClientRect().top;
  const bottomGap=14;
  const available=Math.max(420,window.innerHeight-top-bottomGap);
  grid.style.height=`${available}px`;
  requestAnimationFrame(()=>map.resize());
}

function addMarker(feature){
  const props=feature.properties||{};
  const group=props.GROUPE;
  const cfg=GROUPS[group];
  if(!cfg) return;
  const el=document.createElement('div');
  el.className='websig-marker';
  el.style.background=cfg.color;
  el.title=props.AFFECTATION||group;
  const icon=document.createElement('span');
  icon.textContent=cfg.icon;
  el.appendChild(icon);
  const center=featureCentroid(feature);
  el.addEventListener('click',()=>{
    new maplibregl.Popup({offset:28,maxWidth:'330px'})
      .setLngLat(center)
      .setHTML(popupHtml(props))
      .addTo(map);
  });
  const marker=new maplibregl.Marker({element:el,anchor:'bottom'}).setLngLat(center).addTo(map);
  markers.push({marker,element:el,group});
}

function add3DLayers(data){
  map.addSource('gbeleban-public',{type:'geojson',data});
  Object.entries(GROUPS).forEach(([group,cfg])=>{
    const id=layerId(group);
    map.addLayer({
      id,
      type:'fill-extrusion',
      source:'gbeleban-public',
      filter:['==',['get','GROUPE'],group],
      layout:{visibility:'none'},
      paint:{
        'fill-extrusion-color':cfg.color,
        'fill-extrusion-height':cfg.height,
        'fill-extrusion-base':0,
        'fill-extrusion-opacity':0.88
      }
    });
    map.on('click',id,e=>{
      const f=e.features&&e.features[0];
      if(!f) return;
      new maplibregl.Popup({maxWidth:'330px'}).setLngLat(e.lngLat).setHTML(popupHtml(f.properties||{})).addTo(map);
    });
    map.on('mouseenter',id,()=>map.getCanvas().style.cursor='pointer');
    map.on('mouseleave',id,()=>map.getCanvas().style.cursor='');
  });
}

function fitPublicExtent(data){
  const bounds=new maplibregl.LngLatBounds();
  function visit(coords){
    if(!Array.isArray(coords)) return;
    if(coords.length>=2 && typeof coords[0]==='number' && typeof coords[1]==='number'){
      bounds.extend(coords);
      return;
    }
    coords.forEach(visit);
  }
  (data.features||[]).forEach(f=>visit(f.geometry&&f.geometry.coordinates));
  if(!bounds.isEmpty()) map.fitBounds(bounds,{padding:{top:45,bottom:45,left:45,right:45},maxZoom:14.35,duration:0});
}

function set3D(enabled){
  is3D=enabled;
  const btn=document.getElementById('toggle-3d');
  const note=document.getElementById('websig-mode-note');
  if(btn){
    btn.classList.toggle('active',enabled);
    btn.setAttribute('aria-pressed',enabled?'true':'false');
  }
  if(note){
    note.textContent=enabled
      ? 'Vue 3D : les mêmes groupes sont extrudés avec une couleur et un volume adaptés à leur thématique. Les hauteurs sont symboliques.'
      : 'Vue par défaut : pictogrammes placés sur les équipements du plan d’aménagement.';
  }
  map.easeTo({pitch:enabled?52:0,bearing:enabled?-18:0,zoom:enabled?14.55:14.2,duration:700});
  updateVisibility();
}

async function loadPublicData(){
  const response=await fetch('/api/gbeleban-carte.geojson');
  if(!response.ok) throw new Error('Impossible de charger les données de Gbéléban en carte.');
  publicData=await response.json();
  add3DLayers(publicData);
  (publicData.features||[]).forEach(addMarker);
  fitPublicExtent(publicData);
  updateVisibility();
}

map.on('load',async()=>{
  document.querySelectorAll('.group-toggle').forEach(cb=>cb.addEventListener('change',updateVisibility));
  setupAllGroupsToggle();
  setupSidebarResize();
  sizeWebsigToViewport();

  const btn=document.getElementById('toggle-3d');
  if(btn) btn.addEventListener('click',()=>set3D(!is3D));

  window.addEventListener('resize',sizeWebsigToViewport);

  try{
    await loadPublicData();
  }catch(err){
    console.error(err);
    const note=document.getElementById('websig-mode-note');
    if(note) note.textContent='Les données cartographiques sont temporairement indisponibles.';
  }
});
