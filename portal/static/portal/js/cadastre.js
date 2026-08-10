const osmBasemap=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
  subdomains:'abc',maxZoom:22,attribution:'© OpenStreetMap contributors',updateWhenIdle:true,keepBuffer:2
});
const imageryBasemap=L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{
  maxZoom:22,attribution:'Tiles © Esri',updateWhenIdle:true,keepBuffer:2
});
const parcelRenderer=L.canvas({padding:.35,tolerance:8});
const cmap=L.map('cadastre-map',{zoomControl:true,minZoom:12,maxZoom:22,preferCanvas:true,renderer:parcelRenderer,zoomAnimation:true,fadeAnimation:false}).setView([9.5846,-8.1318],16);
osmBasemap.addTo(cmap);

const basemapControl=L.control({position:'topright'});
basemapControl.onAdd=function(){
  const box=L.DomUtil.create('div','leaflet-bar');
  box.style.background='#fff';box.style.padding='7px 9px';box.style.borderRadius='8px';box.style.boxShadow='0 1px 6px #0002';
  const label=L.DomUtil.create('label','',box);label.style.display='grid';label.style.gap='3px';label.style.fontSize='11px';label.style.fontWeight='700';label.style.color='#173d2f';label.textContent='Fond de plan';
  const select=L.DomUtil.create('select','',label);select.style.minWidth='145px';select.style.padding='5px 7px';select.style.border='1px solid #d9ddd8';select.style.borderRadius='6px';select.style.background='#fff';
  select.innerHTML='<option value="osm">OSM standard</option><option value="imagery">Orthophoto / satellite</option>';
  L.DomEvent.disableClickPropagation(box);L.DomEvent.disableScrollPropagation(box);
  select.addEventListener('change',()=>{
    if(select.value==='imagery'){
      if(cmap.hasLayer(osmBasemap))cmap.removeLayer(osmBasemap);
      imageryBasemap.addTo(cmap);
    }else{
      if(cmap.hasLayer(imageryBasemap))cmap.removeLayer(imageryBasemap);
      osmBasemap.addTo(cmap);
    }
    if(parcelLayer)parcelLayer.bringToFront();
  });
  return box;
};
basemapControl.addTo(cmap);

let parcelLayer=null;
let lotLabelLayer=L.layerGroup().addTo(cmap);
let currentUrbanLayer='';
let selectedParcelLayer=null;
let activeParcelId=null;
let activeRecord=null;
let editingOwnership=null;
let parcelIndex=new Map();
let parcelLoadController=null;

function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function csrfToken(){const m=document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);return m?decodeURIComponent(m[1]):'';}
function fmtArea(value){const n=Number(value);return Number.isFinite(n)?`${n.toLocaleString('fr-FR')} m²`:'—';}
function fmtDate(value){if(!value)return 'date non renseignée';const d=new Date(`${value}T00:00:00`);return Number.isNaN(d.getTime())?value:d.toLocaleDateString('fr-FR');}
function ownerNames(record){const owners=record?.current_owners||[];return owners.length?owners.map(o=>o.owner.display_name).join(' • '):'Aucun propriétaire actuel renseigné';}
function parcelStyle(){return {renderer:parcelRenderer,color:'#111',weight:1,opacity:.88,fillColor:'#fff',fillOpacity:0};}
function highlightLayer(layer){if(selectedParcelLayer&&selectedParcelLayer!==layer&&selectedParcelLayer.setStyle)selectedParcelLayer.setStyle(parcelStyle());selectedParcelLayer=layer;if(layer?.setStyle)layer.setStyle({renderer:parcelRenderer,color:'#e67e22',weight:3,fillColor:'#e67e22',fillOpacity:.06});}

function setMapLoading(visible,text='Chargement du cadastre…'){
  let el=document.getElementById('cadastre-loading');
  if(!el){el=document.createElement('div');el.id='cadastre-loading';Object.assign(el.style,{position:'absolute',zIndex:'900',left:'50%',top:'18px',transform:'translateX(-50%)',background:'#173d2f',color:'#fff',padding:'9px 14px',borderRadius:'999px',fontSize:'12px',fontWeight:'700',boxShadow:'0 6px 20px #0003',pointerEvents:'none'});document.getElementById('cadastre-map').appendChild(el);}
  el.textContent=text;el.style.display=visible?'block':'none';
}

function updateLotLabels(){
  lotLabelLayer.clearLayers();
  if(!parcelLayer||cmap.getZoom()<18)return;
  const visibleBounds=cmap.getBounds().pad(.12);
  const fragment=[];
  parcelLayer.eachLayer(layer=>{
    const p=layer.feature?.properties||{};
    if(!p.lot||!layer.getBounds)return;
    const bounds=layer.getBounds();
    if(!visibleBounds.intersects(bounds))return;
    const center=bounds.getCenter();
    const icon=L.divIcon({className:'lot-label',html:escapeHtml(p.lot),iconSize:null});
    fragment.push(L.marker(center,{icon,interactive:false,keyboard:false}));
  });
  fragment.forEach(marker=>lotLabelLayer.addLayer(marker));
}
let labelTimer=null;
function scheduleLotLabels(){clearTimeout(labelTimer);labelTimer=setTimeout(updateLotLabels,90);}
cmap.on('zoomend moveend',scheduleLotLabels);

async function loadParcels(layerName=''){
  currentUrbanLayer=layerName||'';document.getElementById('parcel-layer-filter').value=currentUrbanLayer;
  if(parcelLoadController)parcelLoadController.abort();parcelLoadController=new AbortController();
  if(parcelLayer){cmap.removeLayer(parcelLayer);parcelLayer=null;}lotLabelLayer.clearLayers();selectedParcelLayer=null;parcelIndex.clear();
  const url='/api/cadastre.geojson'+(currentUrbanLayer?('?layer='+encodeURIComponent(currentUrbanLayer)):'');
  setMapLoading(true);
  try{
    const response=await fetch(url,{signal:parcelLoadController.signal,cache:'no-store'});const data=await response.json();if(!response.ok)return;
    parcelLayer=L.geoJSON(data,{renderer:parcelRenderer,style:parcelStyle,onEachFeature:(feature,layer)=>{const p=feature.properties||{};parcelIndex.set(String(p.id),layer);layer.on('click',()=>{highlightLayer(layer);openParcelCard(p.id);});}}).addTo(cmap);
    if(parcelLayer.getLayers().length)cmap.fitBounds(parcelLayer.getBounds(),{padding:[25,25],maxZoom:17,animate:false});
    if(parcelLayer.bringToFront)parcelLayer.bringToFront();scheduleLotLabels();
  }catch(err){if(err.name!=='AbortError')console.error('Chargement cadastre',err);}finally{setMapLoading(false);}
}

function parcelCardHtml(record){const p=record.parcel||{};const owners=record.current_owners||[];return `<div class="parcel-card-head"><div><small>FICHE PARCELLE</small><h3>Lot ${escapeHtml(p.lot||p.parcelle||p.reference||'—')}</h3></div><button class="parcel-card-close" type="button" aria-label="Fermer">×</button></div><div class="parcel-meta"><div><b>Îlot</b>${escapeHtml(p.ilot||'—')}</div><div><b>Superficie</b>${escapeHtml(fmtArea(p.superficie))}</div><div><b>Section</b>${escapeHtml(p.section||'—')}</div><div><b>Usage</b>${escapeHtml(p.usage||p.properties?.AFFECTATION||'—')}</div></div><div class="owner-summary"><div class="owner-summary-title">Propriétaire${owners.length>1?'s':''} actuel${owners.length>1?'s':''}</div><div class="owner-name">${escapeHtml(ownerNames(record))}</div>${owners.length?owners.map(o=>`<div style="font-size:11px;color:#68736d">${escapeHtml(o.role_label)}${o.share_percentage!==null?` — ${o.share_percentage}%`:''}</div>`).join(''):'<div class="owner-empty">Vous pouvez renseigner le propriétaire depuis la fiche détaillée.</div>'}</div><div class="parcel-card-actions"><button type="button" class="primary" id="parcel-more">Voir plus</button><button type="button" id="parcel-close-card">Fermer</button></div>`;}
async function getParcelRecord(parcelId){const response=await fetch(`/api/cadastre/parcelles/${parcelId}/fiche/`);const data=await response.json();if(!response.ok)throw new Error(data.detail||'Impossible de charger la fiche parcelle.');return data;}
async function openParcelCard(parcelId){activeParcelId=parcelId;const card=document.getElementById('parcel-card');card.classList.add('open');card.innerHTML='<div style="padding:10px">Chargement de la fiche…</div>';try{activeRecord=await getParcelRecord(parcelId);card.innerHTML=parcelCardHtml(activeRecord);card.querySelector('.parcel-card-close').onclick=closeParcelCard;document.getElementById('parcel-close-card').onclick=closeParcelCard;document.getElementById('parcel-more').onclick=openRegistry;}catch(err){card.innerHTML=`<div class="owner-empty">${escapeHtml(err.message)}</div>`;}}
function closeParcelCard(){document.getElementById('parcel-card').classList.remove('open');}
function historyHtml(record){const items=record?.history||[];if(!items.length)return '<div class="owner-empty">Aucun historique enregistré pour ce lot.</div>';return items.map(item=>{const o=item.owner||{};const period=item.start_date||item.end_date?`${fmtDate(item.start_date)} → ${item.is_current?'Aujourd’hui':fmtDate(item.end_date)}`:(item.is_current?'Période actuelle — dates à compléter':'Période non renseignée');return `<article class="history-card ${item.is_current?'current':'old'}" data-ownership="${item.id}"><h4>${escapeHtml(o.display_name)}</h4><span class="badge">${escapeHtml(item.role_label)}</span>${item.is_current?'<span class="badge">Actuel</span>':''}<div class="period">${escapeHtml(period)}${item.share_percentage!==null?` • Quote-part ${item.share_percentage}%`:''}</div>${item.source?`<div style="font-size:10px;color:#777">Source : ${escapeHtml(item.source)}</div>`:''}${item.source_reference?`<div style="font-size:10px;color:#777">Réf. : ${escapeHtml(item.source_reference)}</div>`:''}${o.identity_document_url?`<div><a href="${o.identity_document_url}" target="_blank" rel="noopener" style="font-size:11px">Voir la pièce d’identité</a></div>`:''}<button type="button" class="edit-history" data-id="${item.id}">Modifier cette fiche</button></article>`;}).join('');}
function openRegistry(){if(!activeRecord)return;const modal=document.getElementById('registry-modal');modal.classList.add('open');modal.setAttribute('aria-hidden','false');document.getElementById('registry-title').textContent=`Lot ${activeRecord.parcel.lot||activeRecord.parcel.parcelle||activeRecord.parcel.reference||'—'} — Îlot ${activeRecord.parcel.ilot||'—'}`;renderHistory();resetOwnerForm();}
function closeRegistry(){const modal=document.getElementById('registry-modal');modal.classList.remove('open');modal.setAttribute('aria-hidden','true');}
document.querySelectorAll('[data-close-registry]').forEach(el=>el.addEventListener('click',closeRegistry));
function renderHistory(){const box=document.getElementById('ownership-history');box.innerHTML=historyHtml(activeRecord);box.querySelectorAll('.edit-history').forEach(btn=>btn.addEventListener('click',()=>editHistory(Number(btn.dataset.id))));}
const ownerForm=document.getElementById('owner-form');
function setFormMode(){const type=ownerForm.querySelector('input[name="person_type"]:checked')?.value||'physical';ownerForm.classList.toggle('legal',type==='legal');}
ownerForm.querySelectorAll('input[name="person_type"]').forEach(r=>r.addEventListener('change',setFormMode));
function setValue(name,value){const el=ownerForm.elements[name];if(el)el.value=value??'';}
function resetOwnerForm(){ownerForm.reset();setValue('source','Saisie Urbanisme');setValue('owner_id','');setValue('ownership_id','');editingOwnership=null;setFormMode();document.getElementById('editor-title').textContent='Ajouter un propriétaire';document.getElementById('add-owner').style.display='inline-block';document.getElementById('replace-owner').style.display='inline-block';document.getElementById('save-owner').style.display='none';document.getElementById('cancel-owner-edit').style.display='none';setMessage('','');}
document.getElementById('new-owner-reset').onclick=resetOwnerForm;document.getElementById('cancel-owner-edit').onclick=resetOwnerForm;
function editHistory(id){const item=(activeRecord.history||[]).find(x=>Number(x.id)===Number(id));if(!item)return;editingOwnership=item;const o=item.owner||{};setValue('owner_id',o.id);setValue('ownership_id',item.id);const radio=ownerForm.querySelector(`input[name="person_type"][value="${o.person_type}"]`);if(radio)radio.checked=true;setFormMode();['last_name','first_names','birth_date','birth_place','nationality','profession','legal_name','legal_form','registration_number','tax_number','representative_name','representative_function','phone','email','address','identity_type','identity_number'].forEach(k=>setValue(k,o[k]));setValue('owner_notes',o.notes);setValue('role',item.role);setValue('share_percentage',item.share_percentage);setValue('start_date',item.start_date);setValue('end_date',item.end_date);setValue('source',item.source);setValue('source_reference',item.source_reference);setValue('ownership_notes',item.notes);document.getElementById('editor-title').textContent=`Modifier — ${o.display_name}`;document.getElementById('add-owner').style.display='none';document.getElementById('replace-owner').style.display='none';document.getElementById('save-owner').style.display='inline-block';document.getElementById('cancel-owner-edit').style.display='inline-block';document.querySelector('.registry-editor').scrollTo({top:0,behavior:'smooth'});}
function setMessage(text,type='error'){const el=document.getElementById('owner-form-message');el.textContent=text;el.className=`form-message${text?' show':''}${text?' '+type:''}`;}
async function postForm(url,formData){const response=await fetch(url,{method:'POST',headers:{'X-CSRFToken':csrfToken()},body:formData});const data=await response.json();if(!response.ok)throw new Error(data.detail||'Enregistrement impossible.');return data;}
async function refreshRecord(){activeRecord=await getParcelRecord(activeParcelId);renderHistory();const card=document.getElementById('parcel-card');if(card.classList.contains('open')){card.innerHTML=parcelCardHtml(activeRecord);card.querySelector('.parcel-card-close').onclick=closeParcelCard;document.getElementById('parcel-close-card').onclick=closeParcelCard;document.getElementById('parcel-more').onclick=openRegistry;}}
async function createOwner(mode){if(!activeParcelId)return;const fd=new FormData(ownerForm);fd.set('mode',mode);fd.delete('owner_id');fd.delete('ownership_id');fd.delete('end_date');try{setMessage('Enregistrement en cours…','ok');await postForm(`/api/cadastre/parcelles/${activeParcelId}/proprietaires/`,fd);await refreshRecord();resetOwnerForm();setMessage(mode==='replace'?'Changement de propriétaire enregistré.':'Copropriétaire ajouté.','ok');}catch(err){setMessage(err.message,'error');}}
document.getElementById('add-owner').onclick=()=>createOwner('add');document.getElementById('replace-owner').onclick=()=>{if(confirm('Les propriétaires actuels seront clôturés dans l’historique. Confirmer le changement de propriétaire ?'))createOwner('replace');};
document.getElementById('save-owner').onclick=async()=>{const ownerId=ownerForm.elements.owner_id.value;const ownershipId=ownerForm.elements.ownership_id.value;if(!ownerId||!ownershipId)return;try{setMessage('Mise à jour en cours…','ok');const ownerFd=new FormData(ownerForm);await postForm(`/api/cadastre/proprietaires/${ownerId}/modifier/`,ownerFd);const rightFd=new FormData();['role','share_percentage','start_date','end_date','source','source_reference','ownership_notes'].forEach(k=>rightFd.set(k,ownerForm.elements[k]?.value||''));rightFd.set('is_current',editingOwnership?.is_current&&!ownerForm.elements.end_date.value?'true':'false');await postForm(`/api/cadastre/historique/${ownershipId}/modifier/`,rightFd);await refreshRecord();resetOwnerForm();setMessage('Fiche et période de propriété mises à jour.','ok');}catch(err){setMessage(err.message,'error');}};

loadParcels();
document.querySelectorAll('input[name="urban-layer"]').forEach(radio=>radio.addEventListener('change',()=>{if(radio.checked){document.getElementById('search-results').innerHTML='';closeParcelCard();loadParcels(radio.value);}}));
const form=document.getElementById('parcel-search');const results=document.getElementById('search-results');
form.addEventListener('submit',async e=>{e.preventDefault();const params=new URLSearchParams(new FormData(form));const response=await fetch('/api/cadastre/recherche/?'+params.toString());const data=await response.json();results.innerHTML='';if(!response.ok){results.innerHTML='<p>Accès refusé.</p>';return;}if(!data.results.length){results.innerHTML='<p>Aucune parcelle trouvée.</p>';return;}data.results.forEach(r=>{const b=document.createElement('button');b.type='button';b.className='parcel-result';b.textContent=`${r.couche?('['+r.couche+'] '):''}${r.reference||''} — S:${r.section||'-'} I:${r.ilot||'-'} L:${r.lot||'-'} P:${r.parcelle||'-'}`;b.onclick=()=>{const target=parcelIndex.get(String(r.id));if(target){highlightLayer(target);if(target.getBounds)cmap.fitBounds(target.getBounds(),{padding:[90,90],maxZoom:19,animate:false});openParcelCard(r.id);scheduleLotLabels();}};results.appendChild(b);});});
