# Progetto MREL CdA — stato di avanzamento

> Documento di lavoro per la preparazione della presentazione al Consiglio
> di Amministrazione di Banco BPM sul benchmark MREL cross-bank.
> Ultimo aggiornamento: **19 maggio 2026**. Le modifiche di ogni sessione sono
> documentate nelle sezioni dove appartengono — per i numeri vivi vedi §12,
> per l'audit trail dei fix metodologici vedi §4.1, §4.2, §10.

---

## 📍 Quick reference — dove trovare cosa

> Stato attuale del progetto a colpo d'occhio. Tutte le sezioni qui sotto
> sono **vive** (riflettono lo stato corrente). Le note storiche sono
> incorporate nelle singole sezioni con testo barrato `~~così~~`.

**📊 NUMERI DEFINITIVI (fonte unica per i valori)**: → **[§12 — Tabelle numeriche consolidate post-fix](#12-tabelle-numeriche-consolidate-post-fix-16-maggio-2026)**

**🎯 4 FINDING CHIAVE per il CdA**: → **[§8.1 — I 4 finding consolidati](#81-i-4-finding-chiave-consolidati-per-il-cda-14-maggio-2026)**

**📚 CONTESTO REGOLATORIO E CMDI**: → **[§13 — Approfondimento per il CdA](#13-approfondimento-per-il-cda--contesto-regolatorio-e-di-mercato-18-maggio-2026)**

### Indice completo

| Sezione | Contenuto | Quando guardarla |
|---|---|---|
| §1 | Obiettivo del progetto | Onboarding nuovo lettore |
| §2 | Decisioni metodologiche (data riferimento, peer set, esclusioni, O-SII) | Quando si discute il perimetro |
| §3 | Peer set definitivo (Cluster 1 ITA + Cluster 2 EU) | Per la lista dei 12 peer |
| §3.3 | Copertura template Q4 2025 per ciascun peer | Stato dataset |
| §4 | Ground truth metodologico (verifica template Pillar 3) | Per giustificare esclusioni come BNL |
| §4.1 | Check completezza/normalizzazione + fix duplicazione r0160 | Audit qualità dati |
| §4.2 | Correzione TLAC3 BPM (granularità Rank 2/4 dal PDF) | Audit specifico BPM |
| §5 | Fonti dati (EBA file + regola di precedenza) | Quando serve risalire alla fonte |
| §6 | CBR — stato e gap per cluster | Stato CBR per banca |
| §7 | Open points + stato decisioni tecniche | Cosa resta aperto |
| §8 | Struttura preliminare presentazione 15 min | Outline deck |
| **§8.1** | **I 4 finding chiave consolidati per il CdA** | **Cuore del progetto** |
| §8.2 | Dashboard HTML statica CdA (17 maggio) | Deliverable tecnico |
| §8.3 | Espansione Universe scatter — O-SII europee | Estensione benchmark |
| §9 | Next steps immediati | Cosa fare poi |
| §10 | Verifica coerenza dati (15 maggio) + fix cushion CBR treatment | Audit metodologico chiave |
| §11 | Riferimenti bibliografici MREL (15 paper baseline) | Fonti per giustificare al CdA |
| **§12** | **Tabelle numeriche consolidate post-fix** | **Fonte unica per i numeri** |
| **§13** | **Approfondimento per il CdA — contesto regolatorio e di mercato** | **CMDI + ricerca arricchimento** |

### Convenzioni del documento

- **§12 è la fonte canonica dei numeri**. Tutti i valori vivi nelle altre
  sezioni sono **rettificati per essere coerenti con §12**. Se una sessione
  di lavoro aggiorna §12 (es. nuovo CBR), va propagata in tutte le sezioni
  dove quel valore è citato — non si lasciano numeri "vecchi" ovunque tranne §12.
- Gli **unici** numeri obsoleti che possono comparire nel file sono dentro
  `~~così~~`, esplicitamente come **audit trail di una correzione** (es. nella
  tabella §10 mostriamo `~~+11.80~~ → +11.79 pp` per documentare il fix).
- I 4 finding sono numerati F1 (Cushion), F2 (SNP-heavy), F3 (Sub/TREA #1), F4 (T2/MREL #1).
- Treatment CBR: `ON_TOP` (r0120 esclude CBR), `INCLUDED` (r0120 include CBR), `UNKNOWN`.
- **Perimetri ITA delle mediane**:
  - **5 banche** = perimetro originale §8.1 prima dell'integrazione BPER (14 maggio): {BPM, UniCredit, Intesa, MPS, Mediobanca}
  - **6 banche** = perimetro aggiornato §12.1 con BPER integrato (16 maggio): {BPM, UniCredit, Intesa, BPER, MPS, Mediobanca}
  - **Per il deck CdA usare il perimetro 6 banche** (è quello aggiornato). Per le mediane corrette, sezione §12.1 + §8.1.
- **Perimetro EU mediane**: 3 banche = {AIB, Belfius, Sabadell} — Bank of Ireland in attesa Pillar 3 Q4 2025.

> **Nota sull'ordine fisico**: nel file, **§11 si trova fisicamente tra §8.1 e §8.2**
> per ragioni storiche (era stata scritta come paragrafo metodologico di fianco
> ai finding). L'ordine logico è quello del TOC sopra. Se cerchi una sezione
> e non la trovi dove te l'aspetti, usa il TOC come mappa.

---

## 1. Obiettivo

Riadattare il progetto **mrel-peer-benchmark** — nato come strumento
analitico interno — in una presentazione di 15 minuti per il CdA di Banco
BPM, con focus sugli **insight di posizionamento di BPM rispetto ai peer
sulla capacità MREL**.

- Audience: membri CdA con background bancario/legale (no spiegazioni di
  base su MREL, sì rigore metodologico).
- Tempo: 15 minuti.
- Output: doppio — dashboard live (versione web tipo Render) +
  PowerPoint con screenshot e tabelle.
- Messaggio principale: **insight di BPM vs peer**, non showcase
  tecnologico.

## 2. Decisioni metodologiche prese

### 2.1 Data di riferimento

**Q4 2025 (31.12.2025) per tutte le banche del peer set** che hanno
pubblicato il Pillar 3. Per le banche ancora in attesa di pubblicazione,
tenere posto e integrare appena disponibili. Il CdA vuole il dato più
aggiornato disponibile.

> Decisione presa il 12 maggio 2026.

### 2.2 Perimetro dei peer

Due cluster paralleli, raccontati entrambi nella presentazione.

**Cluster 1 — peer regolamentari italiani.** 8 banche, tutte resolution
entity standalone con disclosure MREL piena.

**Cluster 2 — peer europei di taglia simile.** 4 banche, range TEM
130-400B EUR (BPM = 204B), Eurozona only, modello di business
commerciale-retail comparable, escluse subsidiary di gruppi cross-border
e banche universal/assicurative troppo grandi.

> Decisione presa il 12 maggio 2026.

### 2.3 Esclusioni esplicite dal peer set

| Banca | Motivo esclusione |
|---|---|
| BNL | Subsidiary di BNP Paribas Group → non ha MREL standalone (ground truth confermato: Pillar 3 BNL non contiene template KM2/TLAC1/TLAC3) |
| Crédit Agricole Italia | Subsidiary di Crédit Agricole S.A. → resolution a livello francese |
| Mediobanca Premier | Subsidiary di Mediobanca Group → resolution a livello consolidato |
| Deutsche Bank Italia | Subsidiary di Deutsche Bank AG → resolution a livello tedesco |
| ING Belgie | Subsidiary di ING Groep NV → resolution a livello olandese |
| FinecoBank, Mediolanum, Generali, Sella, Ifis, Illimity, Desio, Sistema, Profilo, CR Asti | LSI/banche minori, business model troppo diverso o senza disclosure MREL piena |
| DNB Bank | Norvegia (SEE, fuori UE), framework regolatorio diverso |
| Swedbank | Svezia (UE non-Eurozona) |
| PKO Bank Polski | Polonia (UE non-Eurozona) |
| KBC Group | Belgio, taglia 380B = 1.9× BPM, modello universal-bancassurance |
| Bankinter | Spagna, taglia 124B sotto la soglia 130B |

### 2.4 Lista 2024 O-SII

La lista ufficiale 2024 O-SII (pubblicata Banca d'Italia/EBA) include 7
banche italiane: UniCredit, Intesa, BPM, BPER, Mediobanca, ICCREA, BNL.
MPS **non è** O-SII 2024. Tuttavia abbiamo deciso di **non usare la lista
O-SII come criterio di inclusione/esclusione** perché:

- MPS pubblica regolarmente il Pillar 3 con template MREL completi (è
  resolution entity italiana standalone);
- BNL pur essendo O-SII non è comparable perché subsidiary BNP Paribas.

> Decisione presa l'11 maggio 2026.

## 3. Peer set definitivo

> Per lo stato di pubblicazione Pillar 3 Q4 2025 per ciascun peer vedi **§3.3**.
> Per la copertura template (KM2, TLAC1, TLAC3) vedi sempre **§3.3**.

### 3.1 Cluster 1 — Italia (8 peer)

| Peer | LEI | Pillar 3 31.12.2025 | Pillar 3 31.12.2024 |
|---|---|---|---|
| Banco BPM (ancora) | 815600E4E6DCD2D25E30 | ✅ dati EBA (77 righe) + [PDF](https://gruppo.bancobpm.it/download/informativa-da-parte-degli-enti-al-pubblico-terzo-pilastro-del-gruppo-banco-bpm-dati-riferiti-al-31-dicembre-2025) | ✅ [IT](https://gruppo.bancobpm.it/media/dlm_uploads/Pillar-3-Dicembre-2024_Documento.pdf) / [EN](https://gruppo.bancobpm.it/media/dlm_uploads/Pillar-3-December-2024_Doc_EN.pdf) |
| UniCredit | 549300TRUWO2CD2G5692 | ✅ [PDF EN](https://www.unicreditgroup.eu/content/dam/unicreditgroup-eu/documents/en/investors/third-pillar-basel/2025/UniCredit-Group-Disclosure-Pillar-III-as-at-31-December-2025.pdf) | ✅ [EN](https://www.unicreditgroup.eu/content/dam/unicreditgroup-eu/documents/en/investors/third-pillar-basel/2024/UniCredit-Group-Disclosure-Pillar-III-as-at-31-December-2024.pdf) |
| Intesa Sanpaolo | 2W8N8UU78PMDQKZENC08 | ✅ [PDF EN](https://group.intesasanpaolo.com/content/dam/portalgroup/repository-documenti/investor-relations/Contenuti/RISORSE/Documenti%20PDF/en_governance/31122025_Pillar3.pdf) | ✅ [IT](https://group.intesasanpaolo.com/content/dam/portalgroup/repository-documenti/investor-relations/Contenuti/RISORSE/Documenti%20PDF/Pillar3/Pillar%203_31122024.pdf) |
| MPS | J4CP7MHCXR8DAQMKIL78 | ✅ [PDF](https://www.gruppomps.it/static/upload/inf/informativa-al-pubblico---dicembre-2025.pdf) | ✅ [PDF](https://www.gruppomps.it/static/upload/inf/informativa-al-pubblico---dicembre-2024.pdf) |
| Mediobanca | PSNL19R2RXX5U3QWHI44 | ✅ [PDF EN](https://www.mediobanca.com/static/upload_new/pil/pillar3_dicembre25_eng1.pdf) | ✅ [IT](https://www.mediobanca.com/static/upload_new/pil/pillar-iii-31-12-2024-revisori.pdf) / [EN](https://www.mediobanca.com/static/upload_new/pil/pillar-iii-31-12-2024-eng-revisori.pdf) |
| BPER | N747OI7JINV7RUUH6190 | ✅ [PDF](https://www.bper.it/sites/default/files/2026-05/Informativa_Pillar3_31122025.pdf) integrato via `data/manual_entries/bper.json` (16 maggio 2026) | ✅ pubblicato (Pillar 3 12.2024 sul sito) |
| ICCREA | NNVPP80YIZGEY2314M97 | ⏳ in attesa pubblicazione | ✅ [PDF](https://www.gruppobcciccrea.it/Altri_Documeni_Pillar/Informativa%20al%20pubblico%20-%20Pillar%203%20al%2031%20dicembre%202024_final.pdf) |
| Cassa Centrale Banca | LOO0AWXR8GF142JCO404 | ⏳ in attesa pubblicazione | ✅ [PDF](https://www.cassacentrale.it/sites/default/files/documents_attachments/GBC%20-%20Informativa%20al%20pubblico%20al%2031.12.2024_signed_signed_0.pdf) |

> Q4 2025 pubblicato: 6/8. Mancanti: ICCREA, Cassa Centrale (attesa giugno-luglio 2026).

### 3.2 Cluster 2 — Europa (4 peer, Eurozona, taglia simile)

| Peer | LEI | Paese | TEM €B | Pillar 3 31.12.2025 |
|---|---|---|---|---|
| Bank of Ireland Group plc | 635400C8EK6DRI12LJ39 | IE | 141 | ⏳ in attesa pubblicazione |
| AIB Group plc | 635400AKJBGNS5WNQL34 | IE | 149 | ✅ [PDF](https://aib.ie/content/dam/frontdoor/investorrelations/docs/resultscentre/pillar3/AIB-Group-plc-Q4-2025-Pillar-3-Disclosures.pdf) |
| Belfius Bank | A5GWLFH3KM7YV2SFQL84 | BE | 191 | ✅ dati EBA (94 righe) |
| Banco de Sabadell, S.A. | SI5RG2M0WQQLZCXKRM20 | ES | 246 | ✅ dati EBA (72 righe) |

> Q4 2025 pubblicato: 3/4. Mancante: Bank of Ireland (disclosure
> semestrale, atteso marzo-aprile 2026).
>
> *Nota storica*: il 12 maggio 2026 sera abbiamo brevemente espanso il
> Cluster 2 a 9 peer (aggiungendo Bankinter, PKO, ING Belgie, DNB,
> Swedbank), poi ripristinato il perimetro originale di 4.

## 3.3 Copertura template Q4 2025 — stato dataset (13 maggio 2026)

| Peer | KM2 | TLAC1 | TLAC3 (mat.+rank) | TLAC3b | Stato |
|---|---|---|---|---|---|
| **Banco BPM** | ✅ 12 | ✅ 21 | ✅ 36 | — | Completo (EBA) |
| **UniCredit** | ✅ 11 | ✅ 10 | ✅ 10 | — | Completo (PDF Pillar 3) |
| **Intesa Sanpaolo** | ✅ 11 | ✅ 10 | ✅ 12 | — | Completo (PDF Pillar 3) |
| **MPS** | ✅ 11 | ✅ 10 | ✅ 9 | — | Completo (PDF Pillar 3) |
| **Mediobanca** | ✅ 8 | ✅ 10 | ✅ 10 | — | Completo (PDF Pillar 3) |
| **AIB Group** | ✅ 11 | ✅ 10 | ✅ 9 | — | Completo (PDF Pillar 3, nuovo manual_entry) |
| **Belfius Bank** | ✅ 12 | ✅ 17 | ✅ 48 | — | Completo (EBA) |
| **Banco Sabadell** | ✅ 12 | ✅ 21 | — | ✅ 22 | Parziale: pubblica TLAC3b con creditor ranking ma layout diverso, non c'è maturity ladder canonico K_97.00 |
| **BPER Banca** | ✅ KM2 completo | ✅ manual_entry | ✅ TLAC3 (rank+mat) | — | Completo (PDF Pillar 3 Q4 2025, manual_entry 16 maggio 2026) |
| ICCREA | ⚠️ 2 | ❌ | ❌ | ❌ | In attesa Pillar 3 Q4 2025 |
| Cassa Centrale | ⚠️ 2 | ❌ | ❌ | ❌ | In attesa Pillar 3 Q4 2025 |
| Bank of Ireland | ❌ | ❌ | ❌ | ❌ | In attesa Pillar 3 Q4 2025 |

**Riepilogo:** 8 peer con tutti e 3 i template (KM2 + TLAC1 + TLAC3 con maturity + creditor ranking), 1 peer con KM2 + TLAC1 + TLAC3b (Sabadell, no maturity), 3 peer in attesa pubblicazione. Aggiornato 16-17 maggio 2026.

> **Modifica al codice del progetto (13 maggio 2026):** estesa la classe
> `BaseBankParser` (`ingestion/missing_banks/base.py`) per supportare
> blocchi `tlac3_maturity` e `tlac3_ranking` (+ `tlac3b_ranking`) nei
> `manual_entries` JSON. Aggiunto parser `AIBParser`. Aggiunto
> `data/manual_entries/aib.json`. Aggiornati i manual_entries di
> UniCredit, Intesa Sanpaolo, MPS, Mediobanca con i nuovi blocchi TLAC3.

## 4. Ground truth metodologico

Verificato manualmente su 4 PDF Pillar 3 (presenza dei template
MREL/TLAC):

| Banca | EU KM2 | EU TLAC1 | EU TLAC3 / 3a / 3b | EU ILAC | Note |
|---|---|---|---|---|---|
| BPM (Q4 2024) | ✅ | ✅ | ✅ TLAC3 | ❌ (esplicitato: non G-SII) | Resolution entity standalone, disclosure piena |
| MPS (Q4 2024) | ✅ | ✅ | ✅ TLAC3a | ❌ | Resolution entity standalone, MREL/TREA = 26.48% |
| BNL (Q4 2024) | ❌ | ❌ | ❌ | ❌ | **Conferma esclusione**: nessun template MREL — è subsidiary di BNP Paribas |
| AIB Group (Q4 2025) | ✅ | ✅ | ✅ TLAC3b | ❌ | Resolution entity standalone irlandese, 41 menzioni MREL |

> Nomenclatura template — varia per banca: "TLAC3", "TLAC3a", "TLAC3b" si
> riferiscono allo stesso concetto (creditor ranking della resolution
> entity) con piccole variazioni redazionali. Tutti i template confluiscono
> nelle stesse celle K_97.00 e K_98.00 dell'export EBA.

## 4.1 Check di completezza e normalizzazione (13 maggio 2026, sera)

Eseguito sistematico check di completezza, unità e coerenza interna sul peer
set Q4 2025 prima di passare all'analisi dei finding.

### Completezza per metrica chiave

| Metrica | Coverage | Banche con dato Q4 2025 |
|---|---|---|
| KM2 MREL/TREA (capacità) | 8/12 | BPM · UniCredit · Intesa · MPS · Mediobanca · AIB · Belfius · Sabadell |
| KM2 MREL requirement | 10/12 | + BPER (parziale) + ICCREA (solo req) + Cassa Centrale (solo req) |
| TLAC1 stack composition | 8/12 | come KM2 MREL |
| TLAC3 maturity profile | 7/12 | come KM2 MREL meno Sabadell (template TLAC3b senza maturity ladder canonico) |
| TLAC3 creditor ranking | 8/12 | (Sabadell via TLAC3b) |
| CBR % + treatment classificato | 11/12 | manca solo Bank of Ireland |

### Quality checks superati ✅

- **Unità coerenti** — tutti i ratios sono decimali, gli amounts in EUR
  (non in migliaia/milioni residui). Verificato per ogni manual_entry.
- **TLAC3 ranking Σ ≈ maturity total** — coincidenza esatta (Δ < 0.1%) per
  UniCredit, Intesa, MPS, Mediobanca, AIB; Belfius Δ 2.35% (rounding EBA);
  Sabadell n/a (template diverso).
- **TLAC1 stack ≈ KM2 MREL totale** — dopo il fix sotto, allineamento entro
  l'1.8% per tutte le banche, il residuo è imputabile a deduzioni Art. 32b
  CRR che il TLAC1 ignora (comportamento documentato).
- **CBR treatment** — 7 banche esplicito da Pillar 3, 3 banche rolled-forward
  (regola: roll-forward del treatment quando in una data precedente è
  esplicito), 1 stimato (Cassa Centrale, treatment esplicito + valore
  stimato), 1 placeholder UNKNOWN (Bank of Ireland).
- **Alignment TLAC1 ↔ TLAC3 ranks** (osservazione Enrico, 13 maggio):
  - r0140 (Senior pre-cap) ↔ K_97.00 Rank 5 (Senior non-preferred) — match esatto
  - r0150 (Senior grandfathered) ↔ Rank 6 (Senior preferred) — match esatto
  - r0160 = r0140 + r0150 = aggregato post-cap (non è una classe aggiuntiva)

### Fix tecnico applicato — `core/metrics.tlac1_composition`

**Problema rilevato:** la formula originale sommava `r0140 + r0150 + r0160`
per `senior_eligible_liabilities`, ma r0160 è l'aggregato post-cap di r0140
e r0150 (= r0140 + r0150 quando nessun cap Art. 72b(3) è applicato). Sommare
tutti e tre **raddoppiava la senior eligible** quando r0160 era popolato.

**Banche affette dalla duplicazione (TLAC1 stack pre-fix):**

| Banca | r0140 | r0150 | r0160 | TLAC1 pre-fix vs KM2 |
|---|---|---|---|---|
| BPM | 5.78 | 0.28 | 6.06 | +27.6% gonfiato |
| MPS | 2.75 | 0.11 | 2.86 | +21.0% gonfiato |
| Mediobanca | 9.83 | 0.00 | 9.83 | +50.8% gonfiato |
| Sabadell | 3.27 | 0.04 | 3.31 | +15.0% gonfiato |

**Fix applicato (13 maggio 2026):**
```
senior_eligible = r0160  if r0160 > 0  else  r0140 + r0150
```

**Post-fix:** TLAC1 stack ≈ KM2 MREL per tutte le banche (Δ < 1.8% ovunque,
spiegabile con deduzioni). I 29 test del progetto continuano a passare.

> **Impatto sui finding:** i finding sulla composizione del peer set
> proposti il 12 maggio (BPM "senior-heavy" 42.8%, Mediobanca 66%) erano
> influenzati dalla duplicazione e vanno **ricalcolati** sulle nuove
> share TLAC1.

## 4.2 Correzione TLAC3 BPM (14 maggio 2026)

Durante l'analisi finding al CdA è emersa una **inconsistenza significativa
nel TLAC3 di BPM** rilevata da Enrico confrontando il template EU TLAC3a
del PDF Pillar 3 con il dato letto dal file Excel EBA.

### Il problema

L'**EBA cell-level export per BPM K_97.00 aggrega Rank 2 e Rank 4 sotto
un'unica voce senza `open_key`** (6.86 mld). Il PDF discloses la
breakdown granulare:

| Rank | Insolvency description (italian SRB master scale, Dlgs 36/2018) | MREL eligible Q4 2025 |
|---|---|---|
| 1 (most junior) | Equity | 12,672 mln |
| 2 | Capital instruments and Subordinated Claims contractually agreed | 3,606 mln |
| 3 | Subordinated liab not qualifying as own funds | 0 mln |
| 4 | **Senior Non-Preferred Debt** (chirografario di secondo livello) | **3,250 mln** |
| 5 | **Unsecured Claims** (Senior Preferred) | **5,780 mln** |
| 6 (most senior) | **Deposits different from those referred under layers IT 6/IT 7** | **281 mln** |
| Σ 1 to n | | 25,589 mln |

Il file EBA invece riportava solo Rank 1, Rank 5, Rank 6 + un valore "no
rank" di 6.86 mld (= 3,606 + 3,250 collassati).

### L'impatto su un'analisi precedente

Con i dati EBA aggregati, avevo mappato erroneamente Rank 5 di BPM come
"Senior Non-Preferred" (=r0140 di TLAC1) → questo mi aveva portato al
**finding errato "BPM = 95% SNP del MREL Eligible Liabilities"**. La
versione corretta è **BPM = 34.9% SNP**, in linea con UniCredit (31.6%)
e Belfius (30.7%), ma **comunque la più alta tra le italiane O-SII**
(mediana ITA ~~14.9%~~ → **14.60% su 5 banche / 14.05% su 6 banche con BPER** —
ricalcolato 19 maggio 2026, vedi §8.1 e §12.1).

### Il fix tecnico applicato (14 maggio 2026)

1. **Nuovo `data/manual_entries/bpm.json`** con TLAC3 granulare dal PDF
   (Rank 1, 2, 4, 5, 6 + maturity ladder completo).
2. **Nuovo parser `ingestion/missing_banks/bpm.py`** + `Source.PDF_BPM`.
3. **Meccanismo `MANUAL_OVERRIDE_KEYS` in `ingestion/normalize.py`**:
   triple `(LEI, template, ref-date)` esplicite per cui il manual_entry
   sovrascrive EBA e datahub. Prima entry: BPM K_97.00 31-12-2025.
4. **Re-ingest** completato (6.645 fatti). BPM TLAC3 Q4 2025 ora ha 11
   righe granulari (5 ranks + 5 maturity buckets + total).

### Lezione metodologica

L'EBA cell-level export può **collassare ranks adiacenti** quando una
banca utilizza una classificazione che non corrisponde 1:1 alla "master
scale" attesa. Per banche con disclosure granulare nel proprio Pillar 3
PDF, conviene **verificare la breakdown** invece di basarsi solo sui
totali aggregati.

## 5. Fonti dati

### 5.1 File EBA cell-level

| File | Contenuto | Stato |
|---|---|---|
| `data/raw/p3mreldata_2025q4.xlsx` | 113 banche × 3 trimestri (Q2/Q3/Q4 2025) | Già nel progetto; **primario** |
| `mrel311225updated.xlsx` (uploaded) | 98 banche solo Q4 2025 | **NON usare**: meno banche, meno italiane O-SII; valori Q4 identici a `p3mreldata_2025q4.xlsx` |

> Verifica del 12 maggio 2026: i due file hanno **valori Q4 2025 identici
> al 100%** (3.120 celle controllate, 0 differenze). Il file "updated" non
> aggiunge informazione ed è meno completo. Resta `p3mreldata_2025q4.xlsx`
> come fonte primaria.

### 5.2 Regola di precedenza per i dati MREL

1. **Se la banca è nel file EBA con Q4 2025 popolato → usa il file EBA.**
2. **Se la banca è nel file EBA solo con Q2 2025 → recupera il Pillar 3
   PDF dal sito ufficiale e popola via `data/manual_entries/<banca>.json`.**
3. **Se la banca non è nel file EBA → recupera dal Pillar 3 PDF e popola
   via `manual_entries`.**

> Regola data da Enrico l'11 maggio 2026.

### 5.3 Manual entries già popolati (da `data/manual_entries/`)

bbva.json · bper.json · cassa_centrale.json · credem.json ·
credit_agricole.json · iccrea.json · intesa.json · mediobanca.json ·
mediolanum.json · mps.json · socgen.json · unicredit.json.

> Alcuni di questi (es. mediolanum, credem, credit_agricole) si
> riferiscono a banche **fuori** dal peer-set definitivo. Sono retaggio
> della prima versione del tool; non devono comparire in dashboard nei
> due cluster, ma restano nel codice come "universo esteso" disponibile
> per analisi ad hoc.

## 6. CBR — stato e gap

Il CBR (Combined Buffer Requirement) non è nell'export EBA cell-level.
Va recuperato dalla narrativa dei Pillar 3 e classificato come:

- `ON_TOP`: la KM2 r0120 mostra il requisito al netto del CBR (convenzione
  filing default — BPM, Intesa, ecc.).
- `INCLUDED`: la KM2 r0120 mostra il requisito già comprensivo di CBR
  (Mediobanca, ICCREA, BBVA).
- `UNKNOWN`: non determinato → si applica fallback breach-test.

### 6.1 Cluster 1 — copertura CBR

| Peer | CBR Q4 2025 | Treatment | Stato |
|---|---|---|---|
| BPM | 3.74% | ON_TOP | ✅ esplicito (Pillar 3 dic 2025 p.27) |
| UniCredit | **4.87%** | **INCLUDED** | ✅ verificato (Pillar 3 dic 2025 EN p.30 — CBR esplicito 4.87%; treatment INCLUDED dedotto: 27.05% realizzato include CBR perché 30.59 < 27.05+4.87) |
| Intesa Sanpaolo | **4.49%** | ON_TOP | ✅ esplicito (Pillar 3 dic 2025 EU KM1 riga 11, verificato 19 maggio 2026) |
| MPS | **3.27%** | **INCLUDED** | ✅ esplicito (Pillar 3 dic 2025 EU KM1 riga 11 = 3.2691%, verificato 19 maggio 2026; treatment roll-forward da Q4 2024 vedi §7.4) |
| Mediobanca | **3.43%** | INCLUDED | ✅ esplicito (Pillar 3 dic 2025 EU KM1 riga 11 = 3.4382%, verificato 19 maggio 2026 — O-SII buffer sceso a zero vs sept 2025) |
| BPER | **3.522%** | **INCLUDED** | ✅ da KM1 p.12 Pillar 3 Q4 2025; treatment INCLUDED inferred via breach-test |
| ICCREA | 3.59% | INCLUDED | ✅ esplicito (Pillar 3 giu 2025 p.40) |
| Cassa Centrale Banca | 3.0% | ON_TOP | ✅ treatment esplicito; valore stimato |

> **Stato definitivo** — tutti i treatment chiusi (vedi §7.4). MPS: valore esplicito da KM1 riga 11 (Pillar 3 dic 2025, 3.2691%), treatment INCLUDED roll-forward da Q4 2024; BPER INCLUDED inferred via breach-test (Pillar 3 Q4 2025 integrato 16 maggio).

### 6.2 Cluster 2 — copertura CBR

| Peer | CBR Q4 2025 | Treatment | Stato |
|---|---|---|---|
| Bank of Ireland | n/d | n/d | ❌ assente — Pillar 3 Q4 2025 in attesa (semestrale, atteso marzo-aprile 2026) |
| AIB Group | **5.44%** | **ON_TOP** | ✅ verificato (Pillar 3 dic 2025 p.6: "MREL = higher of 23.05% TREA, 28.49% including CBR" → 23.05 + 5.44 = 28.49 ✓) |
| Belfius Bank | **5.23%** | **ON_TOP** | ✅ verificato (Pillar 3 dic 2025 p.39: "MREL requirement 23.68% TREA, with CBR 5.23%" → 23.68 + 5.23 = 28.91 ✓) |
| Banco Sabadell | **3.50%** | **INCLUDED** | ✅ PDF P3 EN p.87 nota (1): "requirements include the CBR of 3.50%" |

> **Stato definitivo** — 3 su 4 chiusi (AIB, Belfius, Sabadell). Bank of Ireland in attesa Pillar 3 Q4 2025.

## 7. Open points

### 7.1 Dati in attesa di pubblicazione

| Banca | Cosa manca | Atteso entro | Azione |
|---|---|---|---|
| ~~BPER~~ | ~~Pillar 3 Q4 2025~~ | ~~Maggio-giugno 2026~~ | ✅ Integrato 16 maggio 2026 |
| ICCREA | Pillar 3 Q4 2025 | Giugno-luglio 2026 | Ricontrollare tra 4-6 settimane |
| Cassa Centrale Banca | Pillar 3 Q4 2025 | Giugno-luglio 2026 | Ricontrollare tra 4-6 settimane |
| Bank of Ireland | Pillar 3 Q4 2025 | Marzo-aprile 2026 (potrebbe già esserci, controllare) | Ricontrollare tra 1-2 settimane |
| ~~Intesa Sanpaolo~~ | ~~Versione italiana Pillar 3 Q4 2025~~ | ~~Probabilmente già uscita~~ | ✅ Validato (EN + IT confermati) |

### 7.3 Decisioni tecniche — stato

- ✅ **`core/peers.py` aggiornato (12 maggio 2026)**: aggiunti
  `ITALIAN_PEERS_CDA` (8 banche) e `EU_PEERS_CDA` (4 banche) come LEI
  whitelist, inseriti come primi due elementi in `ALL_PEER_SETS` (quindi
  default automatico nel dropdown del tool). Risoluzione: 8/8 italiane e
  4/4 europee — 100% coverage.
- ✅ **`core/cbr.py` aggiornato (12 maggio 2026)**: 9 entry esplicite o
  rolled-forward per Cluster 1 + 8 entry per Cluster 2 (AIB, Bank of
  Ireland, Belfius, Sabadell × Q2 2025 e Q4 2025). MPS Q4 2024 e Q4 2025
  classificate INCLUDED in coerenza con la regola roll-forward.
  Convenzione confermata: se una banca specifica il treatment in una
  data, lo stesso treatment si applica alle date successive salvo
  disclosure esplicita di cambio.
- ✅ **Re-ingest dei dati lanciato**: `data/processed/facts.parquet`
  (6.670 righe dopo aggiornamenti TLAC3) e `banks.parquet` (121 banche).
- ✅ **`ingestion/missing_banks/base.py` esteso (13 maggio 2026)**:
  aggiunto supporto per blocchi JSON `tlac3_maturity`, `tlac3_ranking`,
  `tlac3b_ranking` nei manual_entries (prima accettava solo `km2` e
  `tlac1`). Schema descritto nel parser.
- ✅ **Nuovo parser AIB Group** (`ingestion/missing_banks/aib.py`) +
  manual_entry (`data/manual_entries/aib.json`) — primo parser
  Cluster 2 con TLAC3 popolato. Aggiunto `Source.PDF_AIB` allo schema.
- ✅ **Manual_entries estesi con TLAC3** per UniCredit, Intesa Sanpaolo,
  MPS, Mediobanca — maturity ladder + creditor ranking estratti dai
  rispettivi Pillar 3 Q4 2025.
- ✅ **`core/metrics.tlac1_composition` corretto (13 maggio 2026)**:
  formula senior_eligible aggiornata a `r0160 if r0160 > 0 else r0140
  + r0150` per evitare il doppio conteggio del valore aggregato post-cap
  (problema rilevato confrontando r0150 di BPM con eligible amount del
  Rank 6 di TLAC3 — Enrico, 13 maggio). Vedi §4.1.
- ✅ **BPM TLAC3 granulare via manual_entry override (14 maggio 2026)**:
  EBA cell-level collassava Rank 2 + Rank 4 di BPM sotto "no open_key".
  Creato `data/manual_entries/bpm.json`, parser `BPMParser`, e
  meccanismo `MANUAL_OVERRIDE_KEYS` in `ingestion/normalize.py` per
  consentire override controllato di EBA/datahub per (LEI, template,
  date) specifici. Vedi §4.2.
- ✅ **Test `test_all_parsers_cover_all_missing_banks` corretto (17 maggio
  2026)**: rinominato da `test_five_parsers_cover_all_missing_banks` e
  reso dinamico (`len(by_lei) == len(ALL_PARSERS)`). Aggiunte asserzioni
  individuali per tutti i 14 parser attuali. Il test ora scala
  automaticamente all'aggiunta di nuovi parser.
- ✅ **29/29 test del progetto passano** (CBR, metrics, ranking,
  composition_maturity, eba_export, p3_datahub, missing_banks).
- ✅ **Scheduled task creato**: `mrel-cda-check-pending-pillar3`,
  fireAt 26 maggio 2026 09:00 CEST. Ricontrollerà BPER, ICCREA, Cassa
  Centrale e Bank of Ireland e produrrà un report con eventuali entry da
  aggiornare in `core/cbr.py` e `manual_entries/`.
- ⚠️ **Decidere se mostrare Mediobanca con caveat**: ha cambiato chiusura
  esercizio (era giugno, ora dicembre per allinearsi a MPS). Il Q4 2025
  è il primo dicembre "ufficiale" per Mediobanca → da segnalare in slide.
- ⚠️ **Aggiornare schermate del tool** dopo re-ingest (PNG in
  `docs/screenshots/` sono ancora quelli vecchi con il peer set
  precedente). Re-runnare `scripts/capture_screenshots.py` con app in
  locale prima del deck CdA.

### 7.4 Stato finale CBR per il peer set CdA

Tutti chiusi tranne le 4 banche in attesa di Pillar 3 Q4 2025.

| Peer | CBR Q4 2025 | Treatment | Esplicito |
|---|---|---|---|
| BPM | 3.74% | ON_TOP | ✅ |
| UniCredit | 4.87% | INCLUDED | ✅ (treatment dedotto da breach-test su valore esplicito CBR) |
| Intesa | **4.49%** | ON_TOP | ✅ (verificato P3 dic 2025 KM1 — agg. 19 maggio 2026) |
| MPS | **3.27%** | INCLUDED | ✅ (valore esplicito Pillar 3 dic 2025 KM1 riga 11 = 3.2691%; treatment roll-forward da Q4 2024) |
| Mediobanca | **3.43%** | INCLUDED | ✅ (verificato P3 dic 2025 KM1 — agg. 19 maggio 2026) |
| BPER | 3.522% | INCLUDED | ✅ (KM1 p.12; treatment inferred via breach-test) |
| ICCREA | 3.59% | INCLUDED | ✅ (roll-forward) |
| Cassa Centrale | 3.0% est. | ON_TOP | ✅ treatment (valore stimato) |
| Bank of Ireland | 4.0% est. | UNKNOWN | ⏳ in attesa P3 Q4 2025 |
| AIB Group | 5.44% | ON_TOP | ✅ |
| Belfius Bank | 5.23% | ON_TOP | ✅ |
| Banco Sabadell | 3.50% | INCLUDED | ✅ |

## 8. Struttura preliminare presentazione 15 min

> Bozza, da raffinare quando avremo dati + 4-5 insight chiave.

| Min | Sezione | Contenuto |
|---|---|---|
| 0-2 | Setup | Perché abbiamo guardato MREL adesso; cosa abbiamo costruito (mossa interna cross-bank vs aggregati EBA/SRB pubblici) |
| 2-4 | Strumento e metodologia | Pipeline dati (EBA + PDF), 8 viste analitiche, tracciabilità per cella, CBR normalization |
| 4-13 | Insight BPM vs peer | 3-4 finding chiave: cushion MREL, composizione stack, profilo maturity, subordinazione — tutti vs Cluster 1 + Cluster 2 |
| 13-15 | Considerazioni e sviluppi | Cosa ci dice sulla posizione di BPM; usi possibili (Tesoreria, Risk, IR); estensioni |

## 8.1 I 4 finding chiave consolidati per il CdA (14 maggio 2026, perimetro aggiornato 16 maggio)

Identificati a partire dai dati Q4 2025 normalizzati. Stato perimetro a 19 maggio 2026:
- **9 banche con Q4 2025 completi**: BPM, UniCredit, Intesa, BPER, MPS, Mediobanca,
  AIB, Belfius, Sabadell (BPER integrata il 16 maggio 2026)
- **3 in attesa** di pubblicazione Pillar 3 Q4 2025: ICCREA, Cassa Centrale, Bank of
  Ireland (scheduled task 26 maggio)

> ⚠️ **Nota su versione 14 maggio vs 19 maggio**: alcune tabelle e numeri di questa
> sezione sono stati calcolati il 14 maggio su perimetro 5 banche ITA + 3 EU (BPER
> non ancora integrata). I numeri sono stati riconciliati il 19 maggio: dove c'è
> divergenza, vince §12.1 (perimetro 6 banche ITA + 3 EU).

### Tabella di sintesi BPM vs peer set (aggiornata 15 maggio 2026)

| Banca | MREL/TREA | Cushion ✅ | Sub/TREA | T2/MREL | SNP%/EL |
|---|---|---|---|---|---|
| **Banco BPM** | 34.02% | **+7.68 pp (#3)** | **24.84% (#1)** | **10.0% (#1)** | **34.9% (#1 ITA)** |
| UniCredit | 30.59% | +3.54 pp | 22.71% | 8.3% | 31.6% |
| Intesa Sanpaolo | 37.28% | +11.79 pp | 21.71% | 8.2% | 14.6% |
| BPER Banca | 27.35% | +1.91 pp | 21.07% | 7.3% | 6.4% |
| MPS | 29.44% | +2.58 pp | 23.26% | 8.0% | 0% |
| Mediobanca | 43.04% | +18.60 pp ⚠️ | 21.94% | 5.2% | 13.5% |
| AIB Group | 35.18% | +6.69 pp | 35.18% | 8.8% | 0% |
| Belfius | 31.19% | +2.28 pp | 22.65% | 7.5% | 30.7% |
| Sabadell | 27.62% | +1.98 pp | 23.49% | 5.9% | 56.0% |

**Mediana ITA (5 banche — perimetro originale §8.1 senza BPER)**: MREL/TREA 34.02% ·
Cushion **+7.68 pp** · Sub/TREA 22.71% · T2/MREL 8.20% · SNP%/EL **14.60%**
*(corretto 19 maggio 2026 — il file precedentemente riportava 14.9% per errore).*

**Mediana ITA (6 banche — perimetro aggiornato §12.1 con BPER integrato)**: MREL/TREA 32.30% ·
Cushion **+5.61 pp** · Sub/TREA 22.33% · T2/MREL 8.10% · SNP%/EL 14.05%
*(numeri di riferimento per il deck CdA — usare questi).*

**Mediana EU (3 banche)**: MREL/TREA 31.19% · Cushion **+2.28 pp** · Sub/TREA 23.49% · T2/MREL 7.50% · SNP%/EL 30.70%.

> ⚠️ Mediobanca: primo esercizio con chiusura dicembre (cambio da giugno per
> allineamento MPS post-merger). Cushion non pienamente comparabile su base YoY.

### Finding #1 — Cushion: BPM #3/9 nel peer set, sopra mediana ITA ✅ (aggiornato 19 maggio 2026)

BPM ha **+7.68 pp** di cushion sopra il requisito lordo (MREL/TREA 34.02%
vs req. lordo 26.34% = req. netto 22.60% + CBR 3.74%). È **#3 su 9** nel
peer set complessivo e **sopra mediana ITA (+5.61 pp su 6 banche)**.

Ranking cushion (9 peer con dati Q4 2025 completi):
Mediobanca +18.60 pp ⚠️ · Intesa +11.79 pp · **BPM +7.68 pp** · AIB +6.69 pp ·
UniCredit +3.54 pp · MPS +2.58 pp · Belfius +2.28 pp · Sabadell +1.98 pp · BPER +1.91 pp.

BPM supera tutti e 3 i peer europei, e UniCredit, MPS, BPER tra gli italiani.
I peer europei hanno requisiti lordi molto più alti (mediana EU 28.49% vs ITA 25.91%)
per effetto di CBR più elevati (AIB 5.44%, Belfius 5.23%), il che comprime
il loro cushion nonostante MREL assoluti simili.

**Storia CdA**: BPM ha spazio strutturale di manovra sopra il requisito
MREL — non per dilution, ma per cushion costruito. Posizionamento solido
sia rispetto al Cluster ITA sia rispetto al Cluster EU.

### Finding #2 — La più SNP-heavy tra le italiane O-SII

BPM ha il **34.9% del MREL Eligible Liabilities in Senior Non-Preferred
Debt** (Rank 4 del template TLAC3a, "strumenti di debito chirografario
di secondo livello" — DLGS 36/2018). Tra le italiane O-SII:

| Banca | SNP % di MREL Eligible Liab |
|---|---|
| **Banco BPM** | **34.9%** |
| UniCredit | 31.6% |
| Intesa | 14.6% |
| Mediobanca | 13.5% |
| BPER | 6.4% |
| MPS | 0% |

BPM è **2.4× la mediana ITA peer set 5 banche (14.60%)** e leggermente sopra la
mediana EU (30.70%). Considerando il peer set ITA aggiornato a 6 banche con BPER
integrato, mediana ITA scende a **14.05%** → **BPM è 2.5× la mediana ITA**. A livello
peer set complessivo, BPM è 2° dietro solo Sabadell (56%).

**Storia CdA**: BPM ha utilizzato **attivamente lo strumento Senior
Non-Preferred** — categoria DLGS 36/2018 art. 91 — per costruire un
buffer subordinato. Strumento più caro da emettere di senior preferred,
ma migliore loss-absorption capacity. **Strategia di funding
"loss-absorption-aware".**

### Finding #3 — Subordinazione totale: BPM #1 del peer set comparable

BPM Sub/TREA = **24.84%** — il valore più alto fra le 8 banche **comparable** del
peer set CdA con dati Q4 2025 completi. AIB Group (Sub/TREA 35.18%) è esclusa
dal ranking per non-comparabilità metodologica: nel framework irlandese a 3 rank
non esiste un SNP separato, ogni unsecured è subordinato ai depositi protetti
quindi Sub/MREL ≈ 100% — non confrontabile con il framework italiano (vedi
§8.1 Caveat). Le altre 3 banche (ICCREA, Cassa Centrale, Bank of Ireland)
sono in attesa di pubblicazione Pillar 3.

| Rank | Banca | Sub/TREA |
|---|---|---|
| 1. | **Banco BPM** | **24.84%** |
| 2. | Sabadell | 23.49% |
| 3. | MPS | 23.26% |
| 4. | UniCredit | 22.71% |
| 5. | Belfius | 22.65% |
| 6. | Mediobanca | 21.94% |
| 7. | Intesa | 21.71% |
| 8. | BPER | 21.07% |
| — | AIB Group | 35.18% (n/c — vedi sopra) |

**Storia CdA**: diretta conseguenza dei Finding #2 (SNP elevato) e #4
(T2 elevato). BPM offre **la più alta protezione assoluta ai
creditori senior preferred** del peer set. Punto distintivo per:
- rating MREL-aware (Moody's, S&P, Fitch valutano subordinazione)
- funding cost sui senior preferred (spread più contenuti)
- resilienza in scenari di stress / bail-in

### Finding #4 — Tier 2 il più alto del peer set (10% MREL)

BPM **Tier 2/MREL = 10.0%** — il più alto del peer set.

| Banca | T2 / MREL stack |
|---|---|
| **Banco BPM** | **10.0%** |
| AIB | 8.8% |
| UniCredit | 8.3% |
| Intesa | 8.2% |
| MPS | 8.0% |
| Belfius | 7.5% |
| BPER | 7.3% |
| Sabadell | 5.9% |
| Mediobanca | 5.2% |

Mediana ITA 8.20% (5 banche) / 8.10% (6 banche con BPER integrato) · mediana EU 7.50% — BPM è sopra entrambe.

**Storia CdA**: il Tier 2 è strumento di **qualità intermedia tra
capitale puro e debito subordinato eligible**. Più Tier 2 = stack
loss-absorbing più "regulatorily blessed" e stabile. Investimento
deliberato sulla qualità del subordinated stack.

### Storia coerente per il deck (tre tempi)

1. **"BPM ha scelto una strategia di funding distinta"** → 34.9% SNP fra
   le italiane O-SII (Finding #2), 10.0% T2 best-in-class (Finding #4)
2. **"La strategia ha prodotto risultati misurabili"** → subordinazione
   totale più alta del peer set (Finding #3) e cushion sopra mediana ITA
   (Finding #1)
3. **"Conseguenze operative concrete"**: rating MREL-aware,
   funding cost sui senior, resilienza in stress

### Caveat e note metodologiche per il deck

- **Mediobanca**: cushion ~~22.3 pp~~ → 18.60 pp (corretto 15 maggio). È il più alto del
  peer set, ma esercizio fiscale anomalo (passaggio da chiusura giugno a chiusura
  dicembre per allinearsi a MPS post-merger). Da segnalare in slide.
- **MPS**: cushion ~~5.9 pp~~ → 2.58 pp (corretto 15 maggio), basso, riflette il
  target SRB pre-merger Mediobanca (nuovo target in fase di calibrazione).
- **AIB Group**: cushion 12.1 pp e Sub/TREA 35.18% sono effetto di
  modello irlandese (legge concorsuale a 3 rank: niente SNP separato,
  tutto è Senior Preferred → ma per BRRD ogni unsecured è subordinata
  rispetto a depositi protetti → Sub/MREL = 100%).
- **Composizione bilanciata vs concentrate**: BPM ha mix
  diversificato. Per contrasto: Mediobanca ha 49% senior eligible +
  zero perpetual (modello issuance-heavy), Intesa 42% senior eligible,
  MPS 67% CET1 + 0% AT1 (modello equity-heavy post-ristrutturazione).

## 11. Riferimenti bibliografici MREL (compilati 15 maggio 2026)

Ricerca sistematica su paper accademici, policy paper istituzionali e
research industry rilevanti per i 4 finding chiave del CdA.
File individuali in `docs/references/` (naming: `<ID>_<autore>_<anno>.md`).

**Finding di riferimento:** F1 = Cushion · F2 = SNP-heavy · F3 = Sub/TREA #1 · F4 = T2 #1

### Tema A — MREL/TLAC vs composizione subordinata (SNP, T2)

| ID | Fonte | Anno | Finding | Priorità |
|---|---|---|---|---|
| A1 | [SRB MREL Policy 2024](https://www.srb.europa.eu/system/files/media/document/MREL%20Policy%202024_clean%20version_web.pdf) | 2024 | F1, F2, F3 | ★★★★★ |
| A2 | [SRB MREL Policy 2023](https://www.srb.europa.eu/system/files/media/document/2023-05-15_SRB_MREL_Policy_2023_final%20_clean.pdf) | 2023 | F1, F2 | ★★★ |
| A3 | [Psaroudakis — MREL in EU Bank Resolution Law (Springer)](https://link.springer.com/chapter/10.1007/978-3-031-19600-3_3) | 2023 | F2, F3 | ★★★ |
| A4 | [Banque de France / ACPR — LAC G-SIBs EU vs US](https://www.banque-france.fr/system/files/2024-05/Resolution%20of%20banking%20crises%20what%20are%20the%20loss%20absorbency%20requirements%20in%20Europe%20and%20the%20United%20States.pdf) | 2024 | F2, F3 | ★★★★ |
| A5 | [BIS FSI Insights No. 69 — Loss-absorbing capacity requirements](https://www.bis.org/fsi/publ/insights69.pdf) | 2023 | F1, F3 | ★★★★ |

### Tema B — Calibrazione requisiti MREL (SRB, EBA, BRRD2, CMDI)

| ID | Fonte | Anno | Finding | Priorità |
|---|---|---|---|---|
| B1 | [EBA — 2nd MREL Impact Assessment Report](https://www.eba.europa.eu/publications-and-media/press-releases/eba-publishes-its-second-mrel-impact-assessment-report) | 2024 | F1, F2 | ★★★★★ |
| B2 | [EBA — Resolution Convergence Report 2024 (EREP)](https://eba.europa.eu/sites/default/files/2024-08/2239bdcc-7324-4971-908a-438db4534ac1/EREP%202024%20convergence%20report%20(EBA-Rep-2024-18).pdf) | 2024 | F1, F3 | ★★★ |
| B3 | [BIS FSI — Restoy, "Can MREL be lower?" (EFDI 2025)](https://www.bis.org/speeches/sp250606.htm) | 2025 | F1 | ★★★★ |
| B4 | [Accordo politico CMDI — Consilium UE / PE](https://www.consilium.europa.eu/en/press/press-releases/2025/06/25/bank-resolution-council-and-parliament-strike-deal-to-strengthen-the-eu-crisis-management-framework/) | 2025-2026 | F2 | ★★★ |
| B5 | [FSB — 2025 Resolution Report (PDF)](https://www.fsb.org/uploads/P210126-1.pdf) | 2026 | F3, F4 | ★★★ |

### Tema C — MREL e bail-in / loss absorption

| ID | Fonte | Anno | Finding | Priorità |
|---|---|---|---|---|
| C1 | [Marqués-Ibáñez et al. (ECB WP 2959) — Bail-in in Action](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2959~85ac7a4b23.en.pdf) | 2024 | F2, F3 | ★★★★ |
| C2 | [Pablos Novo (ECB WP 2317) — Bail-in framework e yield spread](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2317~3a5259cba1.en.pdf) | 2019/2020 | F3, F4 | ★★★ |
| C3 | [Bank of England — Operational Guide to Bail-in Resolution](https://www.bankofengland.co.uk/paper/2026/operational-guide-to-bail-in-resolution) | 2026 | F2, F3 | ★★★ |
| C4 | [FSB — 2024 Resolution Report: "From Lessons to Action"](https://www.fsb.org/uploads/P051224.pdf) | 2024 | F1, F3, F4 | ★★★★ |
| C5 | [FSB — 2023 Resolution Report: "Applying Lessons Learnt"](https://www.fsb.org/uploads/P151223.pdf) | 2023 | F1, F3 | ★★★★ |

### Tema D — MREL cushion, funding cost e spread

| ID | Fonte | Anno | Finding | Priorità |
|---|---|---|---|---|
| D1 | [ING Think — "How preferred is preferred senior?"](https://think.ing.com/articles/bank-outlook-how-preferred-is-preferred-senior/) | 2023 | F2 | ★★★★ |
| D2 | [BIS WP 831 — "Believing in bail-in? Market discipline and pricing"](https://www.bis.org/publ/work831.pdf) | 2020 | F3 | ★★★★ |
| D3 | [EBA Risk Assessment Report — Autumn 2024](https://www.eba.europa.eu/sites/default/files/2024-11/f03ee0c1-7258-4391-8bf1-578924956049/EBA%20Risk%20Assessment%20Report%20-%20Autumn%202024.pdf) | 2024 | F2, F3 | ★★★ |
| D4 | [ESM — "The hidden web: MREL bonds e fondi di investimento"](https://www.esm.europa.eu/blog/hidden-web-how-loss-absorbing-bonds-connect-banks-and-investment-funds) | 2024 | F2 | ★★★ |
| D5 | [Marqués-Ibáñez et al. (ECB WP 2758) — Bank bond holdings e bail-in](https://www.ecb.europa.eu/pub/pdf/scpwps/ecb.wp2758~08c650022e.en.pdf) | 2022 | F2 | ★★★ |

> File individuali con abstract completo e note di rilevanza:
> `docs/references/<ID>_*.md` (15 file, uno per fonte).
> Lista commentata sintetica: `docs/mrel_paper_reference.md`.

---

## 8.2 Dashboard HTML statica CdA (17 maggio 2026)

Generata `dashboard_mrel_cda_2025q4.html` — file HTML self-contained (38 KB)
con dati embedded, nessuna dipendenza da server. Apribile direttamente nel
browser per la presentazione CdA.

**Caratteristiche:**
- Dati fissi al 31-12-2025 (embedded come `const DATA=JSON` al momento della
  generazione).
- Scelta peer set: Cluster 1 ITA (8 banche), Cluster 2 EU (4 banche), entrambi.
- **4 sezioni analitiche:** Cushion (6 metriche selezionabili + 6 badge KPI),
  Composition (stacked bar, toggle 100%/€bn), Maturity (heatmap), Creditor rank
  (stacked bar per insolvency rank).
- **Sidebar filtri section-specific**: i controlli di ogni sezione (metrica,
  sort, view) compaiono nella sidebar solo quando la sezione è attiva.
  Peer set è l'unico filtro sempre visibile.
- **Copertura dati:** KM2=12 banche del peer set (le 3 in attesa hanno valori
  null), Composition=9 (incl. BPER da manual entry), Maturity=8 (excl. Sabadell
  TLAC3b), Creditor rank=8.
- **Generato da:** `scripts/build_dashboard.py` — script rigenerabile (aggiunto
  19 maggio 2026). Legge `data/processed/facts.parquet`, calcola le metriche
  con `core/metrics.py` + `core/cbr.py`, inietta i dati nel template
  `scripts/dashboard_template/dashboard.html.tpl`. L'universe scatter (banche
  extra peer set) è mantenuto separatamente in
  `scripts/dashboard_template/universe.json` perché raccolto manualmente da
  PDF Pillar 3 esterni alla pipeline normale.

**Workflow di rigenerazione (per aggiornamenti futuri):**
```bash
# 1. Aggiorna i dati sorgente (es. core/cbr.py, manual_entries, ecc.)
# 2. Re-ingest:
python scripts/ingest.py
# 3. Rigenera la dashboard HTML:
python scripts/build_dashboard.py
```

**Fix applicati durante generazione (storia 17 maggio 2026):**
- BPER mancante dalla Composition (TLAC1 non nell'EBA export) → supplementato
  dai `data/manual_entries/bper.json` con stessa formula di `core/metrics.py`.
- BPER CBR Q2/Q3 2025 con `source` non conforme al test
  (`test_disclosure_table_is_internally_consistent`) → aggiunto prefisso
  `[default]` nei source string di `core/cbr.py`.

---

## 8.3 Espansione Universe scatter — O-SII europee (17 maggio 2026)

Analisi sistematica delle banche O-SII EBA 2024 (189 banche) per identificare
grandi banche europee con TREA > 12 bn assenti dall'universe scatter.

### Metodologia

1. Download lista O-SII EBA 2024 (pubblicata maggio 2025, 189 entries).
2. Cross-reference contro `facts.parquet` (template K_90.01, r0030/r0040 Q4 2025).
3. Identificazione dei "top missing" per score O-SII: Nordea, Danske, ING Bank,
   KBC Group, Erste Group.
4. Recupero dati TREA + MREL/TREA dai Pillar 3 Q4 2025 ufficiali di ciascuna banca.
5. Aggiunta al universe array in `dashboard_mrel_cda_2025q4.html`.

### Dati estratti dai Pillar 3 Q4 2025

| Banca | LEI | TREA (€bn) | MREL/TREA | Fonte |
|---|---|---|---|---|
| Nordea Bank Abp | 529900ODI3047E2LIV03 | 159.7 | 36.60% | P3 PDF p.162, EU KM2 row 2/3 |
| ING Bank N.V. | 3TK20IVIUJ8J3ZU0QE75 | 340.2 | 31.89% | P3 PDF p.19, EU10/EU12 (sub-cons.) |
| Danske Bank A/S | MAES062Z21O4RZ2U7M96 | 90.2 | 42.15% | P3 XLS EU KM2 (DKK→EUR 7.4605) |
| KBC Group | 213800X3Q9LSAKRUWY91 | 127.6 | 31.43% | P3 XLSX sheet KM2, 31.12.2025 |
| Erste Group | — | n/d | n/d | **Esclusa**: PDF Pillar 3 non accessibile (pagina JS-rendered); stime SRB H1 2025 non sufficientemente precise per TREA resolution group |

> **Note ING Bank**: si usa il dato sub-consolidato ING Bank N.V. (TREA 340.2 bn,
> MREL/TREA 31.89%) anziché il gruppo ING Groep NV — coerente con il perimetro
> resolution group per confronto cross-bank.
>
> **Note Danske Bank**: la banca pubblica in DKK; conversione con tasso BCE
> al 31.12.2025 (7.4605 DKK/EUR). DKK 672,972M → EUR 90.2 bn.
>
> **Note KBC Group**: già nella tabella esclusioni peer set (sezione 2.3) perché
> 1.9× la taglia di BPM e modello universal-bancassurance. Incluso nell'universe
> scatter come benchmark di contesto, non come peer diretto.

### Risultato

`universe` array in `dashboard_mrel_cda_2025q4.html`: da **27 → 31 banche**.
Universe copre ora un range da ~13 bn (Länsförsäkringar) a ~789 bn (BNP Paribas),
con buona densità nella fascia 80–350 bn rilevante per il posizionamento di BPM.

---

## 9. Next steps immediati

✅ **Completati il 12 maggio 2026:**
1. ~~Recuperare CBR mancante per UniCredit, MPS, BPER e i 4 peer Cluster 2~~
   — chiusi 9 su 12; restano BPER e Bank of Ireland in attesa pubblicazione.
2. ~~Aggiornare `core/peers.py` con Cluster 1 (8) e Cluster 2 (4) via LEI
   whitelist~~ — fatto.
3. ~~Re-ingest dei dati~~ — fatto.

✅ **Completati il 13 maggio 2026:**
4. ~~Estendere parser per accettare blocchi `tlac3_maturity`,
   `tlac3_ranking`, `tlac3b_ranking` nei manual_entries.~~
5. ~~Creare nuovo parser/manual_entry AIB Group plc (Cluster 2).~~
6. ~~Estendere i manual_entries di UniCredit, Intesa, MPS, Mediobanca
   con i blocchi TLAC3.~~
7. ~~Eseguire check completezza/normalizzazione su tutto il peer set.~~
8. ~~Fixare la duplicazione `r0140+r0160` in `tlac1_composition` →
   TLAC1 stack ora coerente con KM2 MREL (Δ < 1.8% per tutte le banche).~~

✅ **Completati il 14-17 maggio 2026:**
9. ~~Identificare 3-4 finding chiave~~ — fatto (§8.1).
10. ~~Ricalcolare tabelle composizione/maturity/ranking~~ — fatto (§12).
11. ~~Ricerca paper/temi caldi MREL~~ — fatto (§11).

⏳ **Ancora aperti:**

12. **Aggiornare le schermate** del tool (lanciare l'app in locale + `scripts/capture_screenshots.py`).
13. **Costruire il deck PowerPoint** con screenshot dalla dashboard live.
14. **Integrare `manual_entries`** di ICCREA, Cassa Centrale, Bank of Ireland
    quando lo scheduled task del 26 maggio confermerà la pubblicazione dei Pillar 3 Q4 2025.
    *(BPER già integrato il 16 maggio.)*

## 10. Verifica coerenza dati — risultati (15 maggio 2026)

### Esito generale

**Dataset integro: 0 errori su 41 check** tra manual_entries JSON e
`facts.parquet`. Tutti i valori ingestiti corrispondono esattamente alle
fonti (EBA export per BPM, PDF Pillar 3 per UniCredit/Intesa/MPS/Mediobanca).

### Cross-check interni superati ✅

| Check | Risultato |
|---|---|
| TLAC3 Σranks == total | ✅ OK per tutte e 5 le banche (delta max 0.00%) |
| TLAC1 stack vs KM2 total | ✅ OK (delta < 1.8% = deduzioni Art.32b CRR) |
| MPS TLAC1 apparente delta 3.9% | ✅ Falso allarme: r0130 (senior grandfathered 530M) non incluso nel calcolo automatico — aggiungendolo stack = 13.62B = KM2 ✓ |
| Sub/TREA da TLAC3 ranks vs KM2 | ℹ️ Divergenza strutturale (non errore): KM2 r0050 usa base TLAC1 (own funds + SNP + deduzioni); TLAC3 ranks includono strumenti pre-deduzioni Art.72b |

### Errore identificato: cushion calcolati con requisito = r0120 − CBR per tutte le banche

**Problema**: il requisito usato nel documento era sempre `r0120 − CBR`,
indipendentemente dal treatment. Questo è sbagliato:

- Per banche **ON_TOP** (BPM, Intesa): `r0120` è già il requisito pre-CBR
  → il requisito lordo corretto è `r0120 + CBR`, non `r0120 − CBR`.
  Il cushion era gonfiato di `2 × CBR`.
- Per banche **INCLUDED** (UniCredit, MPS, Mediobanca): `r0120` include già
  il CBR → il requisito lordo corretto è `r0120` (il CBR non va né sommato
  né sottratto per il cushion). Il cushion era gonfiato di `CBR`.

**Formula corretta:**
```
req_netto  = r0120          se ON_TOP   (r0120 esclude il CBR)
req_netto  = r0120 − CBR   se INCLUDED (tolgo il CBR per avere il netto)
req_lordo  = r0120 + CBR   se ON_TOP
req_lordo  = r0120          se INCLUDED
cushion    = MREL/TREA − req_lordo
```

**Tabella con requisito netto, CBR e requisito lordo — Cluster 1 + Cluster 2 Q4 2025:**

| Banca | Cluster | MREL/TREA | Req. NETTO (pre-CBR) | CBR | Req. LORDO (incl. CBR) | Cushion corretto | Cushion prec. | CBR treatment | Fonte CBR |
|---|---|---|---|---|---|---|---|---|---|
| **Banco BPM** | ITA | 34.02% | 22.60% | 3.74% | **26.34%** | **+7.68 pp** | ~~+11.4 pp~~ | ON_TOP | PDF P3 dic 2025 p.27 |
| UniCredit | ITA | 30.59% | 22.18% | 4.87% | **27.05%** | **+3.54 pp** | ~~+8.4 pp~~ | INCLUDED | PDF P3 dic 2025 EN p.30 |
| Intesa Sanpaolo | ITA | 37.28% | 21.00% | **4.49%** | **25.49%** | **+11.79 pp** | ~~+11.80 pp~~ ~~+16.3 pp~~ | ON_TOP | PDF P3 dic 2025 EU KM1 riga 11 (agg. 19 maggio 2026) |
| MPS | ITA | 29.44% | 23.59% | **3.2691%** | **26.86%** | **+2.58 pp** | ~~+5.9 pp~~ | INCLUDED | PDF P3 dic 2025 EU KM1 riga 11 (agg. 19 maggio 2026) |
| Mediobanca | ITA | 43.04% | **21.00%** | **3.4382%** | **24.44%** | **+18.60 pp** | ~~+22.3 pp~~ | INCLUDED | PDF P3 dic 2025 EU KM1 riga 11 (agg. 19 maggio 2026 — verificato via pipeline re-ingest) |
| AIB Group | EU | 35.18% | 23.05% | 5.44% | **28.49%** | **+6.69 pp** | ~~+12.1 pp~~ | ON_TOP | PDF P3 dic 2025 p.6: "28.49% including CBR" |
| Belfius Bank | EU | 31.19% | 23.68% | 5.23% | **28.91%** | **+2.28 pp** | ~~+7.5 pp~~ | ON_TOP | PDF P3 dic 2025 p.39: "with CBR 5.23%" |
| Banco Sabadell | EU | 27.62% | 22.14% | 3.50% | **25.64%** | **+1.98 pp** | ~~+5.5 pp~~ | INCLUDED | PDF P3 dic 2025 EN p.87 nota (1) |

> **Lettura della tabella**: il Req. NETTO è il requisito SRB puro senza buffer
> di conservazione. Il Req. LORDO (= netto + CBR) è la soglia effettiva che la
> banca deve rispettare per non entrare in MDA restriction. Il cushion misura
> quanto MREL eccede il Req. LORDO.
>
> **Verifica CBR Cluster 2 (15 maggio 2026)**: tutti e 3 i trattamenti
> confermati su fonte primaria. AIB: 23.05 + 5.44 = 28.49 ✓ (PDF p.6).
> Belfius: 23.68 + 5.23 = 28.91 ✓ (PDF p.39). Sabadell: `core/cbr.py`
> cita testualmente nota p.87 EN: *"requirements include the CBR of 3.50%"*,
> req incl-CBR 25.64% = ex-CBR 22.14% + CBR 3.50% ✓.
>
> **Verifica CBR Cluster 1 ITA (19 maggio 2026)**: i PDF Pillar 3 dic 2025
> di Intesa, MPS e Mediobanca sono stati letti in primaria sul template
> EU KM1 riga 11 (Combined Buffer Requirement). Risultati:
> - **Intesa: ~~4.48%~~ → 4.4900%** (CCB 2.50 + CCyB 0.31 + SyRB 0.43 + O-SII 1.25)
>   — cushion ricalcolato da +11.80 → **+11.79 pp**.
> - **MPS: roll-forward 3.27% → 3.2691% esplicito** (CCB 2.50 + CCyB 0.0940 +
>   SyRB 0.6751; no O-SII — non O-SII 2024). Il valore precedente era arrotondato
>   ma sostanzialmente corretto; ora è esplicito dal KM1. Cushion **+2.58 pp invariato**.
> - **Mediobanca: ~~3.69%~~ → 3.4382%** (CCB 2.50 + CCyB 0.1499 + SyRB 0.7884 +
>   **O-SII 0.00** — sceso a zero vs 0.25% di settembre 2025, per riallocazione
>   macro-prudential). Cushion **+18.60 pp invariato** (treatment INCLUDED → CBR
>   non entra nel calcolo del cushion).

### Impatto sui finding

- **Finding #2 (SNP), #3 (Sub/TREA), #4 (T2/MREL)**: ✅ **non impattati**,
  derivano da metriche di composizione, non da cushion.
- **Finding #1 (Cushion)**: ✅ **riformulato** — vedi §8.1 aggiornata.
- **Cushion ricalcolato 19 maggio 2026**: solo Intesa cambia di -1 bp (~~+11.80~~
  → **+11.79 pp**) per via del +1 bp di CBR; tutti gli altri invariati.

---

## 12. Tabelle numeriche consolidate post-fix (16 maggio 2026, aggiornata 19 maggio)

> Questa sezione contiene le tabelle **definitive** calcolate dopo tutti i fix:
> (i) fix r0160 doppio conteggio TLAC1, (ii) fix cushion CBR treatment ON_TOP/INCLUDED,
> (iii) override BPM TLAC3 granulare dal PDF, (iv) ingestion BPER Pillar 3 Q4 2025
> (16 maggio 2026), (v) **CBR primari verificati su Pillar 3 dic 2025 EU KM1 riga 11
> per Intesa, MPS, Mediobanca (19 maggio 2026 — dettagli in §10)**.
> La sezione **§8.1** contiene la narrativa dei finding (testo per deck CdA) e resta come
> riferimento descrittivo. La sezione **§10** contiene la metodologia di verifica coerenza dati.
> **Per tutti i valori numerici usare questa sezione §12.**

### 12.1 Tabella di sintesi finding — peer set completo Q4 2025

| Banca | Cluster | MREL/TREA | Req. LORDO | Cushion | Sub/TREA | T2/Stack | SNP%/EL |
|---|---|---|---|---|---|---|---|
| **Banco BPM** | ITA | 34.02% | 26.34% | **+7.68 pp** | **24.84%** | **10.0%** | **34.9%** |
| UniCredit | ITA | 30.59% | 27.05% | +3.54 pp | 22.71% | 8.3% | 31.6% |
| Intesa Sanpaolo | ITA | 37.28% | **25.49%** | **+11.79 pp** | 21.71% | 8.2% | 14.6% |
| BPER Banca | ITA | 27.35% | 25.44% | +1.91 pp | 21.07% | 7.3% | 6.4% |
| MPS (*) | ITA | 29.44% | 26.86% | +2.58 pp | 23.26% | 8.0% | 0% |
| Mediobanca (*) | ITA | 43.04% | 24.44% | +18.60 pp | 21.94% | 5.2% | 13.5% |
| AIB Group | EU | 35.18% | 28.49% | +6.69 pp | 35.18% | 8.8% | 0% |
| Belfius Bank | EU | 31.19% | 28.91% | +2.28 pp | 22.65% | 7.5% | 30.7% |
| Banco Sabadell | EU | 27.62% | 25.64% | +1.98 pp | 23.49% | 5.9% | 56.0% |

> **Mediana ITA (6 banche, incluso BPM e BPER):** MREL/TREA 32.30% · Req. LORDO 25.91% ·
> Cushion **+5.61 pp** · Sub/TREA 22.33% · T2/Stack 8.10% · SNP%/EL 14.05%
> *(Calcolato 19 maggio 2026 con Python su {BPM, UniCredit, Intesa, BPER, MPS, Mediobanca}.
> Sostituisce i valori precedenti ~~+5.13 pp / 22.49% / 10.0%~~ — origine sconosciuta, errati.)*
>
> **Mediana EU (3 banche):** MREL/TREA 31.19% · Req. LORDO 28.49% · Cushion **+2.28 pp** ·
> Sub/TREA 23.49% · T2/Stack 7.50% · SNP%/EL 30.70%
> *(Verificato 19 maggio 2026 con Python su {AIB, Belfius, Sabadell}.)*
>
> BPER: CBR = 3.522% (KM1 p.12); treatment INCLUDED inferred via breach-test
> (capacity 27.35% < req 25.44% + CBR 3.52% = 28.96%). Req. LORDO = disclosed KM2 EU-7 = 25.44%.
>
> (*) Il requisito MREL riportato riflette il target SRB stabilito prima del perfezionamento
> dell'operazione di integrazione con Mediobanca e sarà oggetto di rideterminazione da parte
> dell'Autorità di risoluzione all'esito del processo di fusione (fonte: Pillar 3 MPS dic. 2025).
> I dati di cushion e requisito di entrambe le banche sono pertanto da considerarsi transitori
> e non pienamente comparabili con il resto del peer set.

### 12.2 Composizione TLAC1 stack — share % (post-fix r0160)

> Formula applicata: `senior_eligible = senior_post_cap if > 0 else senior_pre_cap + senior_gf`
> Cinque classi: CET1 · AT1 · Tier 2 · Subord Eligible Liabilities · Senior Eligible Liabilities.
> Stack lordo (ante deduzioni minori). BPER: deduzione investimenti −633M compresa in CET1.

| Banca | Cluster | CET1% | AT1% | T2% | SubEl% | SenEl% | Stack tot. |
|---|---|---|---|---|---|---|---|
| **Banco BPM** | ITA | 42.0% | 6.2% | **10.0%** | **14.6%** | 27.2% | 22.3B |
| UniCredit | ITA | 47.4% | 5.4% | 8.3% | 12.2% | 26.8% | 92.3B |
| Intesa Sanpaolo | ITA | 35.3% | 6.6% | 8.2% | 8.2% | **41.7%** | 115.8B |
| BPER Banca | ITA | 52.7% | 8.3% | 7.3% | 6.7% | 25.1% | 22.6B |
| MPS | ITA | **67.1%** | 0.0% | 8.0% | 3.9% | 21.0% | 13.6B |
| Mediobanca | ITA | 37.8% | 0.0% | 5.2% | 7.8% | **49.3%** | 20.0B |
| AIB Group | EU | 46.9% | 6.9% | 8.8% | **37.4%** | 0.0% | 19.1B |
| Belfius Bank | EU | 50.9% | 2.2% | 7.5% | 12.0% | 27.4% | 22.5B |
| Banco Sabadell | EU | 47.6% | 12.4% | 5.9% | **19.0%** | 15.0% | 22.1B |

> **Lettura per il CdA:**
> - BPM ha la quota SubEl più alta tra le ITA O-SII (14.6% = SNP puri). Conforme a Finding #2.
> - T2% di BPM (10.0%) è il più alto del peer set — conforme a Finding #4.
> - Mediobanca e Intesa hanno stack senior-heavy (49% e 42%) — modelli di finanziamento opposti a BPM.
> - MPS è equity-heavy (67% CET1) — effetto post-ristrutturazione, zero AT1.
> - BPER: CET1% elevato (52.7%) e SubEl basso (6.7%) — stack simile a MPS, poca componente SNP.
> - AIB: SubEl 37% è tutto subordinated loan (framework irlandese a 3 rank, niente SNP separato).

### 12.3 Maturity profile TLAC3 — share % su MREL Eligible Liabilities (Q4 2025)

> 8 banche con maturity ladder. BPER: da TLAC3b rows 6-10 (somma per bucket). Sabadell: template TLAC3b senza bucket ladder — esclusa.

| Banca | Cluster | 1–2y | 2–5y | 5–10y | 10y+ | Perpetual | **<5y** | Mkt-funded |
|---|---|---|---|---|---|---|---|---|
| **Banco BPM** | ITA | 6.9% | **23.6%** | 9.5% | 5.0% | 55.0% | **30.5%** | 45.0% |
| UniCredit | ITA | 8.4% | 13.7% | 19.4% | 1.9% | 56.6% | 22.1% | 43.4% |
| Intesa Sanpaolo | ITA | **15.2%** | 23.4% | 21.2% | 5.2% | 35.0% | 38.6% | 65.0% |
| BPER Banca | ITA | 5.4% | 15.9% | 10.1% | 10.8% | 57.8% | 21.3% | 42.2% |
| MPS | ITA | 4.3% | 14.6% | 19.5% | 0.0% | **61.5%** | 19.0% | 38.5% |
| Mediobanca | ITA | 15.9% | 31.0% | 16.7% | **36.4%** | **0.0%** | 46.9% | **100.0%** |
| AIB Group | EU | 3.6% | 16.1% | 21.3% | 1.4% | 57.5% | 19.7% | 42.5% |
| Belfius Bank | EU | 7.0% | 24.7% | 16.8% | 1.1% | **50.3%** | 31.7% | 49.7% |

> **Colonne chiave:**
> - **<5y** = quota in scadenza entro 5 anni = pressione di rifinanziamento a medio termine.
> - **Mkt-funded** = quota non-perpetual = debito che dovrà essere rinnovato sul mercato.
>
> **Lettura per il CdA:**
> - BPM: 55% perpetual (capitale) + 23.6% in bucket 2–5y. Il "wall" di rifinanziamento
>   SNP è nei prossimi 3–5 anni. Rollover immediato (<2y) contenuto (6.9% vs Intesa 15.2%).
> - BPER: profilo simile a UniCredit e AIB (perp ~58%, <5y 21%). Il 10.8% in 10y+ segnala
>   emissioni LT recenti (T2 bonds 2032-2033 visibili nel Pillar 3 p.80).
> - Mediobanca è l'outlier strutturale: **0% perpetual**, stack interamente market-funded,
>   36% oltre 10 anni. Profilo da investment bank, non da banca commerciale.
> - Intesa ha il rollover immediato più alto (15.2% in <2y) — ma stack 4.5× più grande.
> - MPS: 0% oltre 10y — nessuna emissione LT recente, coerente con profilo post-ristrutturazione.

### 12.4 Creditor ranking TLAC3 — posizione BPM vs peer (Q4 2025)

| Banca | Rank 1 (Equity) | Rank 2 (Sub contr.) | Rank 3 (Sub liab) | Rank 4 (SNP) | Rank 5 (SenPref) | Rank 6 (Deposits) | Totale EL |
|---|---|---|---|---|---|---|---|
| **BPM** | 12,672M | 3,606M | 0 | **3,250M** | 5,780M | 281M | 25,589M |
| UniCredit | 49,723M | 11,307M | — | 11,221M | 24,275M | — | 96,527M |
| Intesa | 40,216M | 16,941M | 1,013M | 8,460M | 47,645M | 665M | 114,940M |
| BPER | 13,630M | 2,775M | — | 1,503M | 4,430M | 1,233M | 23,572M |
| MPS | 7,160M | 1,620M | — | 0 | 2,863M | — | 11,643M |
| Mediobanca | 7,018M | 904M | — | 1,530M | 9,831M | — | 19,282M |
| AIB | 10,634M | 3,011M | — | — | 7,140M | — | 20,785M |
| Belfius | 10,527M | 2,707M + altri | — | 6,162M (Rank 5 EBA) | — | — | 21,146M |
| Sabadell (TLAC3b) | — | — | — | — | — | — | n/d (template diverso) |

> **Nota BPM**: Rank 4 (SNP) = 3,250M = 34.9% degli Eligible Liabilities ex-Equity.
> Rank 5 (Senior Preferred) = 5,780M = principale componente di funding market.
>
> **Nota BPER**: Rank 4 (SNP) = 1,503M = 6.4% dell'EL totale. Rank 6 = 1,233M depositi
> non garantiti non privilegiati — componente assente negli altri peer ITA, specificità strutturale BPER.
>
> **Nota Belfius**: il ranking EBA usa una scala belga con più livelli (11 ranks totali);
> il mapping ai ranks italiani è approssimativo — non comparare direttamente i valori assoluti.

### 12.5 Ranking cushion finale (9 banche, Q4 2025)

| Rank | Banca | Cluster | Cushion | Note |
|---|---|---|---|---|
| 1 | Mediobanca (*) | ITA | +18.60 pp | Requisito pre-merger — vedi nota (*) |
| 2 | Intesa Sanpaolo | ITA | +11.79 pp | |
| **3** | **Banco BPM** | **ITA** | **+7.68 pp** | **Sopra mediana peer set allargato** |
| 4 | AIB Group | EU | +6.69 pp | CBR 5.44% comprime cushion |
| 5 | UniCredit | ITA | +3.54 pp | |
| 6 | MPS (*) | ITA | +2.58 pp | Requisito pre-merger — vedi nota (*) |
| 7 | Belfius Bank | EU | +2.28 pp | CBR 5.23% comprime cushion |
| 8 | Banco Sabadell | EU | +1.98 pp | |
| 9 | BPER Banca | ITA | +1.91 pp | CBR 3.52% INCLUDED; cushion stretto |

> (*) Il requisito MREL riportato riflette il target SRB stabilito prima del perfezionamento
> dell'operazione di integrazione con Mediobanca e sarà oggetto di rideterminazione da parte
> dell'Autorità di risoluzione all'esito del processo di fusione (fonte: Pillar 3 MPS dic. 2025).
> I dati di cushion e requisito di entrambe le banche sono pertanto da considerarsi transitori
> e non pienamente comparabili con il resto del peer set.
>
> **BPM vs peer ITA (6 banche)**: 3° su 6, **sopra mediana ITA (+5.61 pp)** — BPM cushion +7.68 pp.
> **BPM vs Cluster EU (3 banche)**: supera tutti i peer europei per cushion assoluto.
> **BPER**: cushion più stretto del peer set (+1.91 pp); MREL/TREA 27.35% è il più basso tra le ITA.
> **Cluster EU**: CBR molto più alto (mediana 5.23% vs ITA ~3.5%) → cushion strutturalmente
> più basso a parità di MREL assoluto. BPM supera tutti e 3 i peer europei.

---

## 13. Approfondimento per il CdA — contesto regolatorio e di mercato (18 maggio 2026)

> Sezione aggiunta il 18 maggio 2026 dopo ricerche web indipendenti (estese ai paper
> già raccolti in §11) per arricchire i 4 finding con: (a) evidenze di mercato 2025-2026
> non ancora coperte dai paper baseline, (b) impatto del nuovo package CMDI (firmato
> aprile 2026, entrato in vigore maggio 2026, applicazione 11 maggio 2028) su BPM,
> (c) considerazioni operative concrete da portare alla discussione CdA.

### 13.1 Benchmark UE aggiornato (EBA Q2 2025, SRB H1 2025)

Dati MREL aggregati pubblicati nel periodo nov 2025 - mar 2026, **post-baseline §11**.
Tutte le medie EBA sono **ponderate per RWA** (verificato 18 maggio 2026 sulla pubblicazione
EBA del 26 novembre 2025):

| Metrica | Top-Tier banks UE (EBA Q2 2025) | Banco BPM Q4 2025 | Delta BPM |
|---|---|---|---|
| MREL binding incl. CBR (media ponderata) | 28.5% | 34.02% | **+5.5 pp sopra media** |
| Subordination requirement Top-Tier (media ponderata) | 22.0% | 24.84% (Sub/TREA) | **+2.8 pp sopra media** |
| Own funds/TREA Top-Tier (media ponderata) | 21.6% | n.d. (TLAC1) | n.d. |

> ⚠️ **Caveat**: il dato "Own funds/TREA 20.5%" che gira è la **media di sistema** (tutti i
> 304 banks EBA), **non** la media Top-Tier. Per il confronto BPM (Top-Tier) usare 21.6%.

**Fonti** (verificate sul PDF EBA del 26 nov 2025):
- [EBA Q2 2025 MREL Dashboard — press release](https://www.eba.europa.eu/publications-and-media/press-releases/eba-publishes-its-q2-2025-dashboard-minimum-requirement-own-funds-and-eligible-liabilities)
- [SRB MREL Dashboard H1 2025](https://www.srb.europa.eu/system/files/media/document/2025-11-07_MREL-dashboard_H1-2025.pdf)

**Storia CdA**: il dato BPM Q4 2025 non è solo "#3 nel peer set" — è **5.5 pp sopra la
media ponderata Top-Tier UE**. Cushion strutturale, non posizionamento marginale.

### 13.2 Subordination discount sul senior preferred — evidenza diretta su BPM

**Emissione BPM Senior Non-Preferred Green (16 ottobre 2025) — primo European Green
Bond di un financial italiano**:
- Ammontare: **€500 milioni** (verificato 18 maggio 2026 su press release BPM via
  advisor White & Case)
- Maturity 6 anni, call ottobre 2030
- Cedola 3.125% fissa, prezzo emissione 99.799%
- Order book peak **€2.4 bn** da **>110 investitori**
- Distribuzione: AM/fund 57%, Insurance/pension 26%, banks 7%; Italia 22%,
  Francia 32%, Benelux 12%, IE+UK 12%
- Rating attesi: Baa3 Moody's / BB+ S&P / BBB- Fitch / BBB DBRS

**Citazione testuale BPM (press release ufficiale):**
> "the transaction attracted orders from over 110 entities, peaking at EUR 2.4 billion,
> allowing the group to set its tightest spread ever recorded."

> ⚠️ **Sulla "compressione ~40 bps vs emissioni precedenti"**: questo numero **non è
> citato esplicitamente nei materiali ufficiali BPM o IFR**. Probabile sintesi di
> analista o broker. Non riportarlo al CdA come fatto BPM — solo come stima
> indicativa di analista esterno, oppure ometterlo.

**Fonti verificate (18 maggio 2026)**:
- Press release Banco BPM 16 ottobre 2025 (via gruppo.bancobpm.it / White & Case
  comunicato ufficiale advisor)

**Caveat strutturale Italia (Scope Ratings)**: il paper Scope *"EU banks' non-preferred
senior debt not equidistant from preferred senior and Tier 2"* documenta un caso
specifico (**UBI Banca, 2018**) con subordination premium di 35-40 bps:
> "UBI Banca achieved a subordination premium paid at 35bp-40bp for non-preferred
> senior debt versus senior preferred levels."

⚠️ **Importante**: questo è un **data point UBI 2018**, non una **stima media Scope per
il sistema italiano**. Non presentarlo al CdA come "il subordination premium in Italia
è 35-40 bps" perché Scope non fa quell'affermazione. Inoltre Scope **non afferma
esplicitamente** che la depositor preference italiana fosse già "three-tier" — nota
solo l'introduzione del SNP nel 2018 Italian Budget Law.

[Scope Ratings — EU banks' non-preferred senior debt not equidistant](https://www.scoperatings.com/ratings-and-research/research/EN/154136)

**Storia CdA**: la strategia "loss-absorption-aware" del Finding #2 ha prodotto
risultati misurabili sul costo del funding (tightest spread ever — frase di BPM
stessa), ma la *quantificazione* del subordination discount richiederebbe accesso
ai dati IR interni di BPM (curve spread storiche su emissioni comparabili).

### 13.3 Rating agency uplift — il valore della subordinazione documentato da Moody's

**Moody's BPM Upgrade — 25 novembre 2025** (verificato 18 maggio 2026 su Moody's
press action ratings-news/455199 + report PR_465377):

Rating changes:
- Long-term issuer rating: Baa2 → **Baa1**
- Senior unsecured: Baa2 → **Baa1**
- Long-term deposit rating: Baa1 → **A3** (entra in classe A)
- BCA: baa3 → **baa2**
- Outlook: **Stable**

**Driver citati esplicitamente da Moody's (3 driver, in ordine)**:

> "The upgrade of Banco BPM's long-term issuer and senior unsecured debt ratings
> to Baa1 from Baa2 reflects (1) the upgrade of Banco BPM's BCA to baa2 from baa3,
> (2) the unchanged outcome of the Advanced LGF analysis which leads to a
> **one-notch uplift** for the long-term issuer and senior unsecured debt ratings,
> and (3) the unchanged assumption of low probability of government support."

E sui driver del BCA stesso:
> "The upgrade of Banco BPM's BCA to baa2 from baa3 reflects the upgrade of Italy's
> sovereign rating, and also considers its well-established franchise in Italy,
> benefitting from improved asset quality, good revenue diversification and
> profitability."

> ⚠️ **Importante — calibrazione dell'attribuzione**: il +1 notch dall'Advanced
> LGF analysis è un fatto, ma è **UNO dei 3 driver dell'upgrade**, non l'unico.
> L'upgrade è in larga parte trainato dal sovereign upgrade Italia (driver 1
> "BCA upgrade") e dal franchise/asset quality/profittabilità. Al CdA va presentato
> come: *"Moody's mantiene il +1 notch LGF stabile attribuibile alla struttura
> subordinata di BPM, ma il move da Baa2 a Baa1 di novembre 2025 è guidato
> principalmente dal sovereign Italia"*.

**S&P (luglio 2025)**: BBB / A-2 con **Positive Outlook** (confermato post-ritiro
UniCredit). Il sub-agent riassume che l'ALAC ratio robusto supporta il possibile
upgrade — **non ho verificato la citazione testuale S&P direttamente**.

**Fitch (luglio 2025)**: BBB- con **Positive Outlook** (non verificato in primaria).

**Fonti verificate**:
- [Moody's Banco BPM action 25 nov 2025](https://ratings.moodys.com/ratings-news/455199)
- [Moody's Banks Methodology — March 2024](https://ratings.moodys.com/api/rmc-documents/409852)
- ⚠️ S&P e Fitch action: da scaricare in primaria se servono al deck CdA

**Storia CdA**: il Finding #3 (Sub/TREA #1) si traduce in un **+1 notch stabile**
sul senior unsecured Moody's via Advanced LGF analysis — questo è documentato e
imputabile alla composizione subordinata. Il move complessivo Baa2→Baa1 di
novembre 2025 è multifattoriale (sovereign + franchise + LGF) e non va presentato
come "solo grazie alla subordinazione".

### 13.4 Mercato SNP UE 2025-2026 — implicazioni per BPM

**Volumi UE 2025 (fonte ING Think):**
- Senior unsecured: EUR 206 bn YTD (+EUR 18 bn vs 2024)
- **Senior Non-Preferred: EUR 137 bn (+EUR 24 bn) — segmento di crescita più forte**
- Covered bonds: EUR 153 bn (-EUR 3 bn)

**Outlook ING per 2026:**
- Senior preferred: EUR 80 bn (in crescita per redemption pressures)
- SNP: EUR 125 bn (in lieve calo dopo picco 2025)

**Fonte**: [ING Think — Bank bond supply in 2026](https://think.ing.com/articles/bank-bond-supply-in-2026-still-riding-the-wave/)

**Storia CdA**: ING Think prevede che il mercato SNP UE rallenti nel 2026 dopo il
picco 2025, mentre cresca il senior preferred (driver: redemption pressures). Per
BPM con 34.9% di EL in SNP, **il timing per nuove issuance può aspettare** —
opportunità per ottimizzare lo stack esistente (vedi §13.7). ⚠️ *Non ho dati su
quando BPM ha iniziato a emettere SNP rispetto al mercato europeo, quindi
caratterizzazioni tipo "early/mid/late cycle" non sono supportate dai dati in
questo documento*.

**Esempio peer di liability management**: CaixaBank ha annunciato buyback EUR 1.25 bn
SNP 1.375% giugno 2026 per "ottimizzazione MREL stack". Plan 2025-2027 prevede EUR
10 bn SNP (5.5 bn già collocati). Indica trend di mercato verso optimization — BPM
con cushion +7.68 pp può seguire stessa logica.

[CaixaBank SNP buyback press release](https://www.caixabank.com/en/headlines/news/caixabank-has-launched-a-new--1-25-billion-senior-non-preferred-bond-issue-achieving-the-highest-ever-demand-for-this-type-of-bond)

### 13.5 CMDI Package — stato regolatorio e timeline

> Aggiornamento fondamentale: a maggio 2026 il pacchetto CMDI **è entrato in vigore**.
> Riassunto della catena legislativa, perché non era completa nei paper §11.

**Stato a maggio 2026:**
- Accordo politico Consiglio-Parlamento: 25 giugno 2025
- Adozione formale Consiglio: 30 marzo 2026
- Pubblicazione GUUE: **20 aprile 2026**
- Atti pubblicati:
  - **Regolamento (UE) 2026/808** (modifica SRMR)
  - **Direttiva (UE) 2026/806** (modifica BRRD)
  - **Direttiva (UE) 2026/804** (modifica DGSD)
- **Entrata in vigore Regolamento**: 10 maggio 2026
- **Entrata in vigore Direttive**: 20 giorni post-pubblicazione (~10 maggio 2026)
- **Applicazione generale**: 11 maggio 2028
- **Recepimento italiano** entro lo stesso termine (probabile delega in legge di
  delegazione europea 2026-2027, aggiornamento D.Lgs. 180-181/2015)

**Fonti**:
- [Council formally adopts CMDI (Regulation Tomorrow)](https://www.regulationtomorrow.com/2026/03/council-formally-adopts-cmdi-review-trilogue-agreement/)
- [European Parliament Press 26 marzo 2026](https://www.europarl.europa.eu/news/en/press-room/20260323IPR38827/new-rules-to-address-bank-failures-protecting-taxpayers-and-depositors)
- [Clifford Chance briefing aprile 2026 (PDF)](https://www.cliffordchance.com/content/dam/cliffordchance/briefings/2026/04/new-eu-rules-on-bank-crisis-management-and-deposit-insurance-part-1.pdf)
- [Freshfields CMDI at a Glance](https://www.freshfields.com/en/our-thinking/blogs/risk-and-compliance/new-resolution-rules-for-eu-banks-the-cmdi-package-at-a-glance-102mqw7)
- [Ashurst — CMDI Key Changes for Banks](https://www.ashurst.com/en/insights/eu-resolution-framework-reform-key-changes-for-banks-under-the-cmdi-package/)

### 13.6 CMDI — impatti specifici su BPM

#### 13.6.1 Calibrazione MREL: invariata per banche grandi O-SII come BPM

**Punto centrale**: il CMDI **non riduce né rimuove il pilastro 8% TLOF** (Total
Liabilities including Own Funds) come condizione di accesso al SRF. Il framework
SRMR riformato lo rende "raggiungibile" anche per banche deposit-funded grazie al
meccanismo DGS-bridge, **ma solo per banche con Total Assets ≤ EUR 80 bn**.

Per la fascia **Total Assets EUR 30-80 bn** il contributo DGS è cappato al **2.5%
TLOF** (verificato 18 maggio 2026 su Clifford Chance briefing aprile 2026 +
Regolamento UE 2026/808).

> ⚠️ **Nota tecnica sui denominatori**: la soglia di **applicabilità della fascia**
> è in **Total Assets** (TA, voce contabile di bilancio). Il **cap del contributo
> DGS** è invece espresso in **% TLOF** (Total Liabilities including Own Funds).
> Sono due grandezze distinte — non confondere con TEM (Total Exposure Measure,
> denominatore leverage ratio). Per BPM: TA stimati ~€200 bn al 31.12.2025
> (TEM €204 bn è proxy ravvicinato ma non identico).

**BPM con Total Assets > EUR 80 bn è fuori perimetro DGS-bridge** sia per
applicabilità (sopra soglia €80 bn) sia per dimensione (well above €30 bn).

**Conseguenza**: per BPM i floor SRMR generali (16% TREA / 4.75% TEM ex-CRR/BRRD2
per banche con strategia open-bank bail-in) restano pieni, e l'8% TLOF resta
vincolante come condizione di subordinazione. **Nessun alleggerimento meccanico
del requisito MREL** atteso dal CMDI per BPM.

#### 13.6.2 Gerarchia creditori: NO general single-tier preference

**Importante punto da comunicare al CdA — c'era confusione iniziale su questo**:

La proposta originaria della Commissione (aprile 2023) prevedeva l'abolizione della
super-preference e il passaggio a **single-tier general depositor preference** —
tutti i depositi senior a senior unsecured indistintamente.

**Il trilogo l'ha bocciata**. Il testo finale CMDI introduce una **harmonised
three-tier depositor preference**:
1. Depositi coperti (≤ EUR 100k) — super-preference
2. Depositi > EUR 100k di persone fisiche e PMI
3. Altri depositi (corporate, autorità pubbliche non professional)

**Il Senior Preferred unsecured resta JUNIOR al tier (iii) in tutti gli Stati Membri.**

**Per BPM (Italia)**: l'Italia era **già allineata** alla three-tier preference (art.
91 TUB post-recepimento BRRD). CMDI armonizza ma **non modifica la posizione del
SNP italiano** rispetto allo status quo.

**Per altre banche EU (DE, FR, NL pre-CMDI a "single-tier preferred")**: il Senior
Preferred sarà **declassato dopo i depositi non-coperti corporate**.

**Primo caso pilota Moody's — Crédit Mutuel Arkéa, 21 aprile 2026** (verificato 18
maggio 2026 su comunicato Actusnews del 22 aprile 2026):
- **Upgrade del deposit rating LT** (riflette protezione rafforzata per depositanti)
- **Affirmation issuer e Senior Preferred ratings**, ma **outlook revisionato da
  Stable a Negative** ("higher potential loss for holders of those instruments")
- Driver esplicito CMDI nel comunicato Moody's

Citazione dalla press release Arkéa (che riporta motivazione Moody's):
> "On 26 March 2026, the European Union adopted an expansion of the framework for
> bank crisis management and deposit insurance (CMDI). [...] In the event of a
> bank's insolvency, deposits have a higher priority for repayment than 'senior'
> debt. [...] Moody's upgraded the long-term deposit rating, reflecting Moody's
> view that protection for all depositors has been strengthened; and affirmed the
> issuer and Senior Preferred ratings while revising their outlooks from Stable
> to Negative."

> ⚠️ **Importante**: Arkéa è **il primo caso pilota** post-CMDI di Moody's, **non
> una review settoriale conclamata**. Moody's non ha (ad oggi) annunciato
> pubblicamente una review estesa a tutte le banche FR/DE/NL. Ragionevolmente
> attese azioni analoghe ma da monitorare caso per caso. Per il CdA: presentare
> come *"primo segnale di mercato"*, non come trend già materializzato.

[Press release Arkéa 22 aprile 2026 con motivazione Moody's (PDF)](https://www.actusnews.com/en/download/credit-mutuel-arkea/2026/04/22/97731-04212026-press-release-as-a-result-of-new-rules-on-depositor-preference-moodys-is-conducting-a-review-of-credit-mutuel-arkeas-ratings.pdf)

**Storia CdA**:
- Le **banche italiane** (incluse BPM, Intesa, UniCredit) **non subiscono shock
  rating** dal CMDI: erano già allineate.
- Le **banche francesi/tedesche/olandesi**: avranno review meccaniche del rating
  Senior Preferred → potenziale **vantaggio competitivo relativo italiano sui
  funding cost** nei prossimi 12-24 mesi.
- Per BPM: **maggior certezza giuridica** sul ranking SNP e Senior Preferred
  italiani, e **vantaggio competitivo relativo del Senior Preferred italiano**
  rispetto al Senior Preferred francese/tedesco/olandese che subisce
  declassamento nella gerarchia (vedi §13.9 Messaggio 2).

#### 13.6.3 NCWO post-CMDI: armonizzazione del counterfactual UE

Il CMDI **rafforza la robustezza NCWO** della strategia di resolution attraverso
l'armonizzazione della creditor hierarchy. Logica: se in tutti gli Stati Membri
i depositi preferiscono il SNP allo stesso modo, il counterfactual in insolvency
è chiaro e uniforme a livello UE — i bondholders SNP non possono lamentare un
"worse-off" vs liquidation (in liquidation pagano comunque dopo i depositi).

**Per BPM**:
- **Maggior certezza giuridica** della resolution strategy attuale (NCWO test
  uniforme UE)
- **Nessuna pressione strutturale al rialzo né al ribasso** sul requisito MREL
  nel medio termine — il quadro di calibrazione SRB per le grandi O-SII
  italiane resta invariato (vedi §13.6.1)
- Il cushion attuale Sub/TREA 24.84% riflette buffer prudenziale di management,
  conseguenza meccanica delle emissioni passate e strategia di funding
  (Finding #2) — fattori **non attenuati dal CMDI**

> ⚠️ **Nota onestà intellettuale**: in letteratura accademica si argomenta che
> l'armonizzazione NCWO possa ridurre il margine di sicurezza che l'SRB richiede
> sopra il minimo regolamentare. **Non ci sono però evidenze pubbliche SRB** che
> leghino la calibrazione MREL a NCWO concerns. Non costruire scenari operativi
> su questa ipotesi per il CdA.

#### 13.6.4 Banche mid-size in resolution — effetto sistema sull'offerta SNP

Il CMDI introduce una **"reversed burden of proof"** sul PIA (Public Interest
Assessment). Citazione Freshfields/Clifford Chance:
> "The PIA should be negative only where winding up would meet resolution
> objectives 'not only to the same extent as resolution but more effectively'"
> (vs. precedente "to the same extent")

**Effetto a livello Banking Union (fonte: SRB Staff Working Paper Series #3,
dicembre 2023, sull'impact assessment Commission CMDI)**: stimate **26 banche
addizionali** (su 62 originariamente earmarked per liquidation nel ciclo 2022)
potrebbero avere PIA che passa da negativo a positivo, distribuite in **12 Stati
Membri della Banking Union**.

> ⚠️ **Non c'è breakdown pubblico per paese** Italia specifica. L'analisi
> quantitativa rigorosa "quante banche italiane addizionali entrerebbero" **non è
> ad oggi disponibile** su fonte primaria Banca d'Italia o SRB.

**Status attuali peer set ITA**:
- **BCC Iccrea Group** (4° gruppo bancario italiano, ~€175 bn consolidated assets):
  già nel perimetro SRB con MREL Decision a livello consolidato di gruppo
  cooperativo (single point of entry SPE). Il CMDI **non** modifica meccanicamente
  questo status.
- **BPER**: già resolution entity con MREL Decision SRB pubblicamente nota. Il
  riferimento a "perimetri territoriali BPER" precedentemente in questa sezione
  **non è confermabile** su fonte primaria — rimosso.

**Effetto a sistema atteso**: il CMDI potrebbe far entrare nel perimetro
resolution-eligible alcune banche medie regionali oggi destinate a liquidazione
amministrativa nazionale. Nei prossimi 3-5 anni possibile **aumento offerta SNP/T2
italiane** da queste banche, ma il dimensionamento esatto è **da monitorare** —
non un dato disponibile oggi.

#### 13.6.5 Timeline operativa MREL post-CMDI per BPM

| Periodo | Evento atteso |
|---|---|
| 2026 (giu-dic) | EBA mandato a sviluppare RTS su PIA, DGS least-cost test, deposit eligibility MREL |
| H2 2026 | SRB Public Consultation MREL Policy post-CMDI (probabile) |
| H2 2026 | EBA consultation RTS deposit eligibility (probabile) |
| 2027 | Probabile revisione SRB MREL Policy. **Primo MREL Decision integrato CMDI per BPM** atteso nel ciclo 2027 (dati 31.12.2026, applicabile 1° gennaio 2028) |
| 11 maggio 2028 | Piena applicazione CMDI |
| 2028-2029 | Prima MREL Decision pienamente "post-CMDI" per BPM |

**Fonti**:
- [SRB Work Programme 2026 (PDF)](https://www.srb.europa.eu/system/files/media/document/2025-11-26_SRB-Work-Programme-2026.pdf)
- [EBA Work Programme 2026 (PDF)](https://www.eba.europa.eu/sites/default/files/2026-01/36d4da18-b7f3-48b8-91e1-ac0cf794e364/EBA%20Work%20programme%202026%20final%20(republished%20to%20align%20with%20final%20SPD%202026%20-%202028).pdf)

### 13.7 Opportunità di liability management per BPM

Sintesi delle opportunità tattiche che emergono dai dati Q4 2025 + contesto regolatorio.
**Premessa**: il CMDI è regolatoriamente neutro per BPM (vedi §13.6) — le opportunità
sotto derivano da dati di mercato attuali e dalla composizione dello stack BPM, non
da un alleggerimento del quadro MREL.

1. **Tactical SNP optimization (driver: mercato, non regulator)**: il cushion +7.68 pp
   sopra il requisito lordo dà spazio per non rinnovare al 100% gli SNP outstanding
   che arrivano a call date nel 2026-2027, riducendo carry cost. ⚠️ **L'entità
   economica esatta non è quantificata in questo documento**: per stimarla
   correttamente serve la maturity ladder degli SNP BPM specifici outstanding con
   call date 2026-2027 + le cedole specifiche + un assunto sul costo opportunità
   di rifinanziamento — informazioni che devono venire da Tesoreria/IR BPM. Driver
   esterno: spread di mercato attuali (vedi §13.2) + esempio peer CaixaBank EUR 1.25 bn
   buyback giugno 2026.

2. **Mix rebalancing Sub vs Senior — con cautela**: in teoria possibile sostituire al
   margine SNP costoso con Senior Preferred più economico per ottimizzare il funding
   cost complessivo. ⚠️ **Importante**: il #1 sub/TREA del peer set è valore
   Moody's-blessed (+1 notch sul senior unsecured, vedi §13.3) — **non stravolgere**
   la struttura per inseguire risparmi marginali. La soglia 8% TLOF resta vincolante
   per BPM post-CMDI (DGS-bridge non si applica, vedi §13.6.1).

3. **Hold the cushion**: dato che (a) il dibattito Restoy 2025 va verso "more MREL"
   non meno, (b) il SRB ha confermato che il framework MREL non sarà oggetto di
   recalibrazione stand-alone, (c) il CMDI non riduce i floor SRMR per BPM,
   **mantenere cushion > 3-4 pp resta best practice**.

4. **No new SNP issuance immediata**: con order book 4.8× su ultima emissione e
   spread tightest-ever, BPM ha "stock di credibilità" sul segmento ma il timing
   per nuove issuance può aspettare. Logica: emettere solo per refinancing, non
   per crescita.

### 13.8 Open points emersi dalla ricerca (da approfondire o monitorare)

- **Timeline esatta pubblicazione MREL Policy post-CMDI dell'SRB** — open. Probabile
  H2 2026 ma date non confermate.
- **Calibrazione finale dell'add-on MREL discrezionale post-CMDI per O-SII grandi** — open. Atteso H2 2027.
- **Quantum esatto del recepimento italiano** in materia di gerarchia creditori
  (Italia già allineata, ma servirà aggiornamento tecnico del TUB) — open.
- **Impatto fusione MPS-Mediobanca su requisito MREL combined entity**: boards
  approvano merger plan 10 marzo 2026, effective end of 2026. SRB ricalibrerà il
  requisito MREL nel ciclo di resolution planning 2026 (probabile final decision
  Q4 2026 / Q1 2027). Per il benchmark CdA al 31.12.2025 i dati pre-merger restano
  i corretti — caveat da aggiungere in slide.
- [Mediobanca-MPS merger plan press release](https://www.mediobanca.com/static/upload_new/pre/press-release-eng-v25-rev-wc-def.pdf)

### 13.9 Sintesi per il CdA — 3 messaggi chiave

> Da affiancare ai 4 Finding di §8.1 come **contesto rinforzativo**, non sostitutivo.

**Messaggio 1 — "Il +1 notch LGF di Moody's è la prova diretta del valore della subordinazione":**
La composizione subordinata di BPM (Finding #2-#3-#4) si traduce in un **+1 notch
stabile** sul senior unsecured Moody's via Advanced LGF analysis — questo è
**documentato e attribuibile direttamente** alla struttura subordinata. L'upgrade
complessivo Baa2→Baa1 del 25 novembre 2025 è invece **multifattoriale** (sovereign
upgrade Italia + franchise + asset quality + LGF) — al CdA non va presentato come
"solo grazie alla subordinazione". Sul fronte funding: BPM ha registrato il
"tightest spread ever recorded" sull'emissione SNP del 16 ottobre 2025 (frase di
BPM stessa) — la quantificazione del subordination discount richiede dati IR.

**Messaggio 2 — "CMDI è neutro per BPM, vantaggio competitivo relativo vs banche EU":**
Il package CMDI in vigore da maggio 2026 (applicazione 2028) non modifica
materialmente il profilo MREL di BPM (Total Assets > €80 bn, fuori DGS-bridge;
Italia già allineata a three-tier preference). **Vantaggio competitivo**: il
**Senior Preferred** di banche francesi, tedesche, olandesi sarà declassato
dietro ai depositi corporate (prima era allo stesso livello) — Moody's ha già
fatto un primo caso pilota su Crédit Mutuel Arkéa (21 aprile 2026: outlook
Senior Preferred passato da Stable a Negative). **BPM e altre italiane non
subiscono questo declassamento** perché l'Italia era già allineata. Possibile
compressione spread Senior Preferred italiani vs Senior Preferred francesi/tedeschi
nei prossimi 12-24 mesi — **ipotesi di mercato, non fatto già materializzato**.

**Messaggio 3 — "Cushion solido, opportunità tattiche di mercato (non regolatorie)":**
Il cushion +7.68 pp è strutturalmente **+5.5 pp sopra la media ponderata Top-Tier
UE** (EBA Q2 2025: 28.5% MREL/TREA Top-Tier vs 34.02% BPM) e va mantenuto come
"appropriate insurance" (Restoy BIS giugno 2025). **Non rilassarlo strutturalmente** —
il CMDI non riduce il requisito MREL di BPM e il dibattito regolatorio va verso
"more MREL" non meno. Le opportunità di liability management tattico (non-renewal
selettivo di SNP costosi alla call date, mix rebalancing al margine, no new
issuance salvo refinancing) emergono dai **dati di mercato 2025-2026** (esempio
CaixaBank EUR 1.25 bn buyback giugno 2026), **non da un alleggerimento del quadro
regolatorio**. ⚠️ **Quantificazione economica per BPM non disponibile in questo
documento** — richiede maturity ladder SNP outstanding + analisi cost-of-carry da
Tesoreria/IR.

---

*Documento autogenerato dal lavoro di analisi del 11-18 maggio 2026. Da
mantenere allineato man mano che le decisioni evolvono.*
