// Day 'N' Nite - For Local Strudel Installation
// These patterns should work with your local setup

// Basic pattern using the correct syntax
s("bd sd [~ bd] sd,hh*16, misc")

// Day 'N' Nite style beat
s("bd ~ bd ~, ~ sd ~ sd, hh*8")

// With Roland TR-808 samples
s("bd sd,hh*16").bank("RolandTR808")

// Alternative with TR-909
s("bd sd,hh*16").bank("RolandTR909")

// Full Day 'N' Nite arrangement
s("bd ~ bd ~, ~ sd ~ sd, hh*8").bank("RolandTR808")
