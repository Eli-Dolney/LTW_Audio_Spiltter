// LTW Audio v2 — Demo building blocks (paste into strudel.cc)
// Generated-style output with dynamics, compression, and section stacks

setcpm(32.5);

// Key hint: .scale("c:minor")

let drum_pat = "bd ~ sd ~ bd ~ sd ~"
let bass_pat = "c2 ~ g1 ~ c2 ~ g1 ~"
let melody_pat = "c4@2 ~ e4 ~ g4 ~"
let chord_pat = "C Am F G"

let drums  = s(drum_pat).bank("RolandTR808").gain(0.9)
let bass   = note(bass_pat).sound("gm_synth_bass_1").lpf(400).gain(1.1)
let melody = note(melody_pat).sound("triangle").lpf(1800).delay("0.25:0.4")
let chords = chord(chord_pat).sound("sawtooth").lpf(900).room(0.4).sustain(1.5)

let intro  = drums
let verse  = stack(drums, bass)
let chorus = stack(drums, bass, melody, chords)

chorus
