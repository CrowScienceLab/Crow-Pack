/* Crow Science Lab: shared 2px rounded line system. */
const line = path => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="crow-svg-icon">'+path+'</svg>';
const CrowIcons = {
logo: '<img src="../../assets/crow_pack.png" alt="" class="crow-brand-image">',
folder: line('<path d="M3 7h7l2 2h9v11H3Z M3 7V4h7l2 3"/>'),
file: line('<path d="M6 2h8l4 4v16H6Z M14 2v5h5"/>'),
openArchive: line('<path d="M3 8h7l2 2h9l-3 10H3Z M3 8V4h7l2 3h7v3"/>'),
newArchive: line('<path d="m3 6 9-4 9 4v13l-9 4-9-4Z m0-13 9 4 9-4 M12 10v13 M8 4l9 4v5"/>'),
extractHere: line('<path d="M12 2v12m-5-5 5 5 5-5 M3 15v6h18v-6"/>'),
extractCustom: line('<path d="M3 7h7l2 2h9v12H3Z M12 10v7m-3-3 3 3 3-3"/>'),
isoDisc: line('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2"/><path d="m6 6 3 3m6 6 3 3"/>'),
pdfOptimize: line('<path d="M5 2h10l4 4v16H5Z M15 2v5h4 M8 11h8m-8 4h6m-6 4h4"/>'),
update: line('<path d="M20 8a8 8 0 1 0 0 8 M20 3v5h-5"/>'),
association: line('<path d="m10 8 3-3a4 4 0 0 1 6 6l-3 3 M14 16l-3 3a4 4 0 0 1-6-6l3-3 m1 5 6-6"/>'),
addFile: line('<path d="M6 2h8l4 4v16H6Z M9 13h6m-3-3v6"/>'),
delete: line('<path d="M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>'),
test: line('<path d="m12 2 8 3v7q0 6-8 10-8-4-8-10V5Z m-4 10 3 3 5-6"/>'),
codepage: line('<circle cx="12" cy="12" r="10"/><path d="M2 12h20 M12 2q-8 10 0 20 8-10 0-20"/>'),
cancel: line('<path d="m6 6 12 12M18 6 6 18"/>'),
info: line('<circle cx="12" cy="12" r="10"/><path d="M9 8a3 3 0 1 1 4 3q-1 1-1 3 M12 18h.01"/>'),
settings: line('<path d="m9 3 1-2h4l1 2 3 2 3 1v4l-2 2v2l2 2-2 4-3-1-2 2h-4l-1-2-3-1-3-1v-4l2-2V9L3 7l2-4 3 1Z"/><circle cx="12" cy="11" r="3"/>'),
tools: line('<path d="M14.7 6.3a4 4 0 0 0-5-5l2.1 2.1-2.4 2.4-2.1-2.1a4 4 0 0 0 5 5L4 17l3 3 7.7-8.3a4 4 0 0 0 5-5l-2.1 2.1-2.4-2.4Z"/>'),
convert: line('<path d="M4 7h11m-3-3 3 3-3 3M20 17H9m3 3-3-3 3-3"/>'),
batch: line('<path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z"/>'),
cbz: line('<path d="M4 3h13a3 3 0 0 1 3 3v15H7a3 3 0 0 1-3-3Z M7 3v18 M10 8h7m-7 4h7m-7 4h5"/>'),
privacy: line('<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 4v3"/>'),
split: line('<path d="M4 5h5a3 3 0 0 1 3 3v8a3 3 0 0 0 3 3h5M4 19h5a3 3 0 0 0 3-3V8a3 3 0 0 1 3-3h5m-3-3 3 3-3 3m0 8 3 3-3 3"/>')
};
CrowIcons.extract=CrowIcons.extractHere;
window.CrowIcons=CrowIcons;
