import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// Translations
const resources = {
  en: {
    translation: {
      welcome: "Nexus Station",
      subtitle: "// SYSTEM: ONLINE // MODE: GENESIS",
      draft_placeholder: "Describe your vision...",
      scan_btn: "RUN SECURITY SCAN",
      light_meter: "Light Meter",
      status: "Status:",
      send: "Send Signal",
    },
  },
  fr: {
    translation: {
      welcome: "Station Nexus",
      subtitle: "// SYSTÈME : EN LIGNE // MODE : GENESE",
      draft_placeholder: "Décrivez votre vision...",
      scan_btn: "LANCER SCAN SÉCURITÉ",
      light_meter: "Jauge de Lumière",
      status: "Statut :",
      send: "Envoyer le Signal",
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "en", // Langue par défaut
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
