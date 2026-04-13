/**
 * 状态管理 - 应用全局状态
 */
const state = {
  projects: [],
  currentProject: null,
  chapters: [],
  characters: [],
  relations: [],
  foreshadows: [],
  currentChapter: null,
  currentOutline: null,
  isWriting: false,
  step: 'project'  // project | outline | chapters | writing
};

function resetProjectState() {
  state.projects = [];
  state.currentProject = null;
  state.chapters = [];
  state.characters = [];
  state.relations = [];
  state.foreshadows = [];
  state.currentChapter = null;
  state.currentOutline = null;
  state.isWriting = false;
  state.step = 'project';
}

function setStep(step) {
  state.step = step;
}

function setCurrentProject(project) {
  state.currentProject = project;
}

function setCurrentChapter(chapter) {
  state.currentChapter = chapter;
}

function setChapters(chapters) {
  state.chapters = chapters;
}

function setCharacters(characters) {
  state.characters = characters;
}

function setRelations(relations) {
  state.relations = relations;
}

function setForeshadows(foreshadows) {
  state.foreshadows = foreshadows;
}

function setOutline(outline) {
  state.currentOutline = outline;
}

function setIsWriting(val) {
  state.isWriting = val;
}

window.stateManager = {
  state,
  resetProjectState,
  setStep,
  setCurrentProject,
  setCurrentChapter,
  setChapters,
  setCharacters,
  setRelations,
  setForeshadows,
  setOutline,
  setIsWriting
};