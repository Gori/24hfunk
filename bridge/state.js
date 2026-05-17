// In-memory cache. New WS clients get a snapshot on connect.
const state = {
  section: null, // last SectionState object (from director / fake-section)
  bpm: 78,
  notes: [], // ring buffer of recent note-ons
  lastBeat: null,
};

const NOTE_RING = 64;

function setSection(section) {
  state.section = section;
  if (section && typeof section.bpm === 'number') state.bpm = section.bpm;
}

function pushNote(note) {
  state.notes.push(note);
  if (state.notes.length > NOTE_RING) state.notes.shift();
}

function setBeat(beat) {
  state.lastBeat = beat;
  if (beat && typeof beat.bpm === 'number') state.bpm = beat.bpm;
}

function snapshot() {
  return {
    type: 'snapshot',
    section: state.section,
    bpm: state.bpm,
    notes: state.notes,
    lastBeat: state.lastBeat,
  };
}

module.exports = { state, setSection, pushNote, setBeat, snapshot };
