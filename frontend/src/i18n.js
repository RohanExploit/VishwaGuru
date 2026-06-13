import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import hi from './locales/hi.json';
import mr from './locales/mr.json';
import es from './locales/es.json';
import bn from './locales/bn.json';
import ta from './locales/ta.json';
import te from './locales/te.json';
import ml from './locales/ml.json';
import kn from './locales/kn.json';
import gu from './locales/gu.json';
import pa from './locales/pa.json';
import fr from './locales/fr.json';
import de from './locales/de.json';
import ja from './locales/ja.json';
import zh from './locales/zh.json';
import ru from './locales/ru.json';
import ar from './locales/ar.json';
import pt from './locales/pt.json';
import it from './locales/it.json';
import ko from './locales/ko.json';
import tr from './locales/tr.json';
import vi from './locales/vi.json';
import id from './locales/id.json';
import th from './locales/th.json';
import ur from './locales/ur.json';
import or from './locales/or.json';
import as from './locales/as.json';
import fa from './locales/fa.json';
import nl from './locales/nl.json';
import pl from './locales/pl.json';
import mai from './locales/mai.json';
import ne from './locales/ne.json';
import sa from './locales/sa.json';
import el from './locales/el.json';
import he from './locales/he.json';
import sv from './locales/sv.json';
import ms from './locales/ms.json';
import uk from './locales/uk.json';
import sw from './locales/sw.json';
import tl from './locales/tl.json';
import ro from './locales/ro.json';
import kok from './locales/kok.json';
import ks from './locales/ks.json';
import no from './locales/no.json';
import doi from './locales/doi.json';
import sd from './locales/sd.json';
import mni from './locales/mni.json';
import da from './locales/da.json';
import fi from './locales/fi.json';
import brx from './locales/brx.json';
import hu from './locales/hu.json';
import cs from './locales/cs.json';
import uz from './locales/uz.json';
import lo from './locales/lo.json';
import my from './locales/my.json';
import sat from './locales/sat.json';

const resources = {
  en: { translation: en },
  hi: { translation: hi },
  mr: { translation: mr },
  es: { translation: es },
  bn: { translation: bn },
  ta: { translation: ta },
  te: { translation: te },
  ml: { translation: ml },
  kn: { translation: kn },
  gu: { translation: gu },
  pa: { translation: pa },
  fr: { translation: fr },
  de: { translation: de },
  ja: { translation: ja },
  zh: { translation: zh },
  ru: { translation: ru },
  ar: { translation: ar },
  pt: { translation: pt },
  it: { translation: it },
  ko: { translation: ko },
  tr: { translation: tr },
  vi: { translation: vi },
  id: { translation: id },
  th: { translation: th },
  ur: { translation: ur },
  or: { translation: or },
  as: { translation: as },
  fa: { translation: fa },
  nl: { translation: nl },
  pl: { translation: pl },
  mai: { translation: mai },
  ne: { translation: ne },
  sa: { translation: sa },
  el: { translation: el },
  he: { translation: he },
  sv: { translation: sv },
  ms: { translation: ms },
  uk: { translation: uk },
  sw: { translation: sw },
  tl: { translation: tl },
  ro: { translation: ro },
  kok: { translation: kok },
  ks: { translation: ks },
  no: { translation: no },
  doi: { translation: doi },
  sd: { translation: sd },
  mni: { translation: mni },
  da: { translation: da },
  fi: { translation: fi },
  brx: { translation: brx },
  hu: { translation: hu },
  cs: { translation: cs },
  uz: { translation: uz },
  lo: { translation: lo },
  my: { translation: my },
  sat: { translation: sat }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: false,

    interpolation: {
      escapeValue: false,
    }
  });

export default i18n;