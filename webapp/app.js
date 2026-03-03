const tg = window.Telegram && Telegram.WebApp;
if (tg) {
  tg.expand();
  tg.BackButton.show();
  tg.BackButton.onClick(() => tg.close());
}

let myMap;
let hexagons = [];
let activeTariff = 'all';

function clearHexagons() {
  hexagons.forEach(p => myMap.geoObjects.remove(p));
  hexagons = [];
}

function renderHexagons(data) {
  clearHexagons();
  data.forEach(h => {
    const polygon = new ymaps.Polygon(
      [h.vertices],
      { hintContent: 'x' + h.coefficient },
      {
        fillColor: h.color,
        fillOpacity: 1,
        strokeColor: 'rgba(100,50,180,0.25)',
        strokeWidth: 0,  // Remove borders between hexagons
      }
    );
    myMap.geoObjects.add(polygon);
    hexagons.push(polygon);
  });
}

function getColor(coeff) {
  const t = Math.min(Math.max((coeff - 1.0) / 1.0, 0), 1);
  const r = Math.round(200 - 120 * t);
  const g = Math.round(180 - 160 * t);
  const b = Math.round(255 - 55 * t);
  return `rgb(${r},${g},${b})`;
}

function renderTop(data) {
  const list = document.getElementById('top-list');
  list.innerHTML = '';
  data.forEach(d => {
    const li = document.createElement('li');
    const color = getColor(d.coefficient);
    li.innerHTML = `<span>${d.zone_name} <small>(${d.tariff})</small></span>
      <span class="kef-badge" style="background:${color};color:#fff;">x${d.coefficient}</span>`;
    list.appendChild(li);
  });
}

async function refresh() {
  try {
    const tariffParam = activeTariff !== 'all' ? '&tariff=' + activeTariff : '';
    const [hexRes, topRes] = await Promise.all([
      fetch('/api/hexgrid?' + (activeTariff !== 'all' ? 'tariff=' + activeTariff : '')),
      fetch(`/api/top?n=5${tariffParam}`),
    ]);
    renderHexagons(await hexRes.json());
    renderTop(await topRes.json());
  } catch (e) {
    console.error('Refresh failed:', e);
  }
}

// Filter chips
document.querySelectorAll('.chip').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeTariff = btn.dataset.tariff;
    refresh();
  });
});

// Init Yandex Map
ymaps.ready(function () {
  myMap = new ymaps.Map('map', {
    center: [55.7558, 37.6173],
    zoom: 10,
    controls: ['zoomControl', 'geolocationControl'],
  });
  refresh();
  setInterval(refresh, 30000);
});
