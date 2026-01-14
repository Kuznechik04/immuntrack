const farben = [
  "#f44336", // rot: schlecht
  "#ff9800", // orange
  "#ffeb3b", // gelb
  "#4caf50"  // grün: gut
];

const iso3to2 = {
  DEU: "DE",
  FRA: "FR",
  ITA: "IT",
  USA: "US",
  LKA: "LK"
};

Object.entries(impfstatus).forEach(([landIso, percent]) => {
  const p = Number(percent);

  let farbe;
  if (p >= 80) farbe = farben[3];      // grün
  else if (p >= 50) farbe = farben[2]; // gelb
  else if (p >= 20) farbe = farben[1]; // orange
  else farbe = farben[0];              // rot

  const id2 = iso3to2[landIso] || landIso;
  const element =
    document.getElementById(landIso) ||
    document.getElementById(id2);

  if (element) element.style.fill = farbe;
});
