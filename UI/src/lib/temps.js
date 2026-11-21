/**
 * Textes d'heure de l'écran (pastille « Time »). Moins d'une heure : « 10 min » ; sinon l'heure à la
 * québécoise (« 17 h 30 »), précédée du jour si ce n'est pas aujourd'hui (« lun. 8 h 30 »).
 */
export function texteMinutes(minutes) {
  return `${Math.max(0, Math.round(minutes))} min`;
}

/** « 05:30 PM » (heure prévue renvoyée par le serveur STM) → « 17 h 30 ». */
export function heureQuebec(texte) {
  const m = /^(\d{1,2}):(\d{2})\s*(AM|PM)?$/i.exec(String(texte ?? "").trim());
  if (!m) return String(texte ?? "");
  let h = Number(m[1]) % 12;
  if (m[3] && m[3].toUpperCase() === "PM") h += 12;
  if (!m[3]) h = Number(m[1]);
  return `${h} h ${m[2]}`;
}

const JOURS_COURTS = { demain: "demain", lundi: "lun.", mardi: "mar.", mercredi: "mer.", jeudi: "jeu.", vendredi: "ven.", samedi: "sam.", dimanche: "dim." };

/** Départ exo : { minutes, heure, jour } → texte de la pastille. */
export function texteDepart(d) {
  if (!d.jour && d.minutes < 60) return texteMinutes(d.minutes);
  return d.jour ? `${JOURS_COURTS[d.jour] ?? d.jour} ${d.heure}` : d.heure;
}
