// LTW Audio v2 — Demo remix preset (Phat Analog style)
// In the app, this is generated from YOUR song's extracted patterns

setcpm(32.5);

let drum_pat = "bd ~ sd ~ bd ~ sd ~"
let bass_pat = "c2 ~ g1 ~ c2 ~ g1 ~"
let melody_pat = "c4@2 ~ e4 ~ g4 ~"
let chord_pat = "C Am F G"

let drums  = s(drum_pat).bank("RolandTR808").gain(0.9)
let bass   = note(bass_pat).sound("gm_synth_bass_1").lpf(400).gain(1.1)
let melody = note(melody_pat).sound("triangle").lpf(1800).delay("0.25:0.4")
let chords = chord(chord_pat).sound("sawtooth").lpf(900).room(0.4).sustain(1.5)

window.drums = drums;
window.bass = bass;
window.melody = melody;
window.chords = chords;

stack(
  window.drums.clip(1.5).speed(0.9),
  window.bass.sound("fmsynth").lpf(300).gain(1.3).clip(1.2),
  window.melody.sound("celesta").room(0.8).delay("0.375:0.6"),
  window.chords.sound("juno").lpf(500).lpq(5)
)
