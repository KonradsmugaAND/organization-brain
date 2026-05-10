# Scenariusz wideo — WenetBrain
**Długość:** 30 sekund  
**Styl:** Minimalistyczny SaaS motion, ciemne tło, czyste UI, płynne przejścia  
**Nastrój:** Spokojny → napięcie (problem) → ulga → pewność siebie  
**Paleta:** Tło `#0A0A0F` (głęboka czerń), tekst biały, akcenty `#6366F1` (indygo), `#10B981` (zieleń sukcesu)  
**Muzyka:** Ambient minimal — cichy, lekko narastający beat (styl: Rival Consoles / Jon Hopkins)

---

## Ujęcia z timestampami

---

### [0:00 – 0:04] HOOK — Problem

**Wizualia:**  
Czarne tło. Z mgły wyłaniają się — jeden po drugim, z subtelnym blur-in — trzy karteczki post-it w stylu UI (animowane, nie zdjęcia):

> 🗓 „Ustaliliśmy na spotkaniu…"  
> 📋 „Ktoś miał to sprawdzić…"  
> ❓ „Kiedy to było? Kto ma zadzwonić?"

Karteczki lekko drżą, jakby ktoś chciał je złapać — i znikają w prawo (swipe off screen).

**Tekst overlay** (centrum, duży, biały, thin font):  
```
Każde spotkanie kończy się ustaleniami.
```
*(pojawia się litera po literze, 0.8s delay)*

**Animacja:** Fade in z góry, lekki parallax depth  
**Kamera:** Static, minimalne subtelne zoom-in 0→2%

---

### [0:04 – 0:08] PROBLEM — Napięcie

**Wizualia:**  
Ekran delikatnie pulsuje czerwonym glow na krawędziach (ledwie widoczne).  
Centrum: jedna, prosta linia tekstu.

**Tekst overlay** (centrum, duży, biały, thin font):  
```
Większość z nich znika.
```
*(0.3s delay po poprzednim, pojawia się szybko — uderzenie)*

Po 1.5 sekundy tekst rozpływa się (dissolve), tło wraca do czystej czerni.

**Animacja:** Tekst — quick fade in, slow fade out z lekkim blur  
**Kamera:** Static

---

### [0:08 – 0:14] TRANSITION — Rozwiązanie się pojawia

**Wizualia:**  
Od lewej strony wjeżdża — jak karta na stół — ciemny panel UI aplikacji WenetBrain. Styl: zaokrąglone rogi, subtelny glow border `#6366F1`, glassmorphism.

Na panelu widać:
- Falę audio (waveform) — animowana, pulsująca
- Pod nią tekst transkrypcji pojawia się w czasie rzeczywistym, słowo po słowie:  
  *„…spotkanie w sprawie launchu, termin 15 czerwca, Marek odpowiedzialny za…"*
- Z prawej strony transkryptu wyświetlają się wyodrębniające się tagi:  
  `✅ Action item` `📌 Decyzja` `📅 Termin`

**Tekst overlay** (górna część, mały, szary):  
```
Nagraj. Wgraj. Resztą zajmie się WenetBrain.
```

**Animacja:** Panel — ease-out slide z lewej, 0.6s  
Transkrypcja — typewriter effect, 60 chars/s  
Tagi — pop-in jeden po drugim z 0.15s przerwą  
**Kamera:** Powolne zbliżenie na panel (zoom 0→8%)

---

### [0:14 – 0:20] SHOWCASE — Wiedza się organizuje

**Wizualia:**  
Panel transkrypcji zmniejsza się do lewej kolumny.  
Z prawej wysuwa się druga kolumna — lista zadań:

```
□  Marek — przygotować brief do 15.06
□  Asia — potwierdzenie z klientem
□  Kamil — review landing page
```

Każde zadanie pojawia się z góry na dół z lekkim bounce.  
Ikona ClickUp (mała, subtelna) miga przy zadaniach — sugerując eksport.

W tle (bardzo subtelnie, rozmyte) widać sidebar z przestrzeniami:  
`🔒 Prywatne` · `👥 Zespół` · `🏢 Firma`

**Tekst overlay** (centrum, duży):  
```
Zadania. Decyzje. Wiedza.
Wszystko w jednym miejscu.
```
*(dwa wiersze pojawiają się z 0.5s opóźnieniem między sobą)*

**Animacja:** Slide-in kolumny, stagger children  
**Kamera:** Powolny pan prawo→lewo, 4%

---

### [0:20 – 0:26] AI CHAT — Kulminacja

**Wizualia:**  
Pełnoekranowe ujęcie na okno czatu. Minimalistyczne, ciemne.  
Kursor pojawia się w polu input i pisze:

> *„Co powinienem zrobić w tym tygodniu?"*

Enter. 0.5s ładowania (trzy kropki).  
Pojawia się odpowiedź AI — płynnie, jak stream:

> *„Masz 3 zadania z ostatnich spotkań: brief dla Marka (do 15.06), potwierdzenie klienta od Asi oraz…"*

Pod odpowiedzią widoczne linki do źródeł:  
`📎 Spotkanie launch — 12.06` `📎 Review call — 10.06`

**Tekst overlay** (brak — UI mówi samo za siebie)

**Animacja:** Typing cursor — naturalny ritm  
Odpowiedź — token streaming effect  
Source citations — fade in po 0.3s od końca odpowiedzi  
**Kamera:** Lekkie zbliżenie na chat (zoom 0→5%), bardzo wolne

---

### [0:26 – 0:30] OUTRO — Logo i tagline

**Wizualia:**  
UI znika (fade out z lekkim blur).  
Czyste czarne tło.  
Centrum ekranu:

**Logo** `WenetBrain` — pojawia się z dissolve, font bold, biały  
Pod spodem po 0.4s:

> *Twoja firma pamięta wszystko.*

Delikatny glow indygo pod logotypem, pulsujący raz.

**Animacja:** Logo — scale 0.95→1.0 + fade in  
Tagline — fade in, lighter weight  
Końcowe 0.5s: freeze frame  
**Kamera:** Static

---

## Wskazówki do generowania AI (Sora / Runway / Kling)

Każde ujęcie generuj osobno jako 4–6 sekundowy clip, łącząc w edytorze.

**Prompt bazowy (styl):**
```
Dark SaaS product demo video, minimalist UI motion graphics, deep black background #0A0A0F, 
indigo accent glow #6366F1, clean sans-serif typography, smooth ease-out animations, 
glassmorphism UI panels, cinematic subtle camera movement, Apple/Linear aesthetic, 
no people, no stock footage, pure motion design, 4K, 60fps
```

**Ujęcie 1–2 (karteczki/tekst):**
```
Floating sticky note UI cards appearing one by one on dark background, soft blur entrance, 
minimalist design, then disappearing with swipe right motion, followed by large centered 
white text "Większość z nich znika" appearing with quick fade
```

**Ujęcie 3 (transkrypcja):**
```
Dark glassmorphism UI panel sliding in from left, audio waveform animating inside, 
real-time transcription text appearing word by word, colored tag chips popping in 
on the right side labeled "Action item" "Decision" "Deadline", indigo glow border
```

**Ujęcie 4 (task list):**
```
Split UI panel, left side transcription, right side task list items appearing 
with stagger animation top to bottom, subtle ClickUp integration icon, 
background showing navigation sidebar with workspace levels
```

**Ujęcie 5 (AI chat):**
```
Minimal dark chat interface, typing cursor entering question text, 
three-dot loading animation, then AI response streaming in token by token, 
source citation chips appearing below, clean modern design
```

**Ujęcie 6 (outro):**
```
Clean black background, centered bold white logotype "WenetBrain" fading in 
with subtle indigo glow underneath, tagline "Twoja firma pamięta wszystko" 
appearing below in light weight, single glow pulse, freeze
```

---

## Format eksportu

| Parametr | Wartość |
|----------|---------|
| Rozdzielczość | 1920×1080 (16:9) lub 1080×1920 (9:16 — social) |
| FPS | 60 fps |
| Długość | 30 sekund ±2s |
| Format | MP4 H.264 |
| Muzyka | Fade out ostatnie 3 sekundy |
