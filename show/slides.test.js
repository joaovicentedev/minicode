import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import slides from "./slides.js";

const { createPresentation, formatElapsed, moveSlide } = slides;

test("HTML opens as a local file with only the first slide visible", () => {
  const html = readFileSync(new URL("./apresentacao.html", import.meta.url), "utf8");
  const sections = html.match(/<section class="slide[^>]*>/g) ?? [];
  assert.equal(sections.length, 11);
  assert.equal(sections[0].includes(" hidden "), false);
  assert.ok(sections.slice(1).every(section => section.includes(" hidden ")));
  assert.match(html, /<script defer src="slides\.js"><\/script>/);
});

test("formatElapsed shows minutes and seconds and clamps negatives", () => {
  assert.equal(formatElapsed(125.9), "02:05");
  assert.equal(formatElapsed(-10), "00:00");
});

test("moveSlide stays within the deck", () => {
  assert.equal(moveSlide(0, -1, 3), 0);
  assert.equal(moveSlide(1, 1, 3), 2);
  assert.equal(moveSlide(2, 1, 3), 2);
});

test("createPresentation navigates and updates timer", () => {
  const element = () => ({ textContent: "", style: {}, disabled: false, listeners: {}, addEventListener(key, callback) { this.listeners[key] = callback; } });
  const slides = [0, 1, 2].map(() => ({ hidden: false, dataset: { title: "Teste" }, setAttribute() {} }));
  const nodes = { "#slide-count": element(), "#timer": element(), "#progress": element(), "#previous": element(), "#next": element() };
  const doc = { title: "", listeners: {}, querySelectorAll() { return slides; }, querySelector(key) { return nodes[key]; }, addEventListener(key, callback) { this.listeners[key] = callback; } };
  let now = 0;
  let tick;
  const deck = createPresentation(doc, () => now, callback => { tick = callback; });
  assert.equal(nodes["#slide-count"].textContent, "01 / 03");
  assert.deepEqual(slides.map(slide => slide.hidden), [false, true, true]);
  deck.navigate(1);
  assert.equal(nodes["#slide-count"].textContent, "02 / 03");
  now = 65000;
  tick();
  assert.equal(nodes["#timer"].textContent, "01:05");
  doc.listeners.keydown({ key: "Home", preventDefault() {} });
  assert.equal(nodes["#slide-count"].textContent, "01 / 03");
  doc.listeners.keydown({ key: "r", preventDefault() {} });
  assert.equal(nodes["#timer"].textContent, "00:00");
  nodes["#next"].listeners.click();
  assert.equal(nodes["#slide-count"].textContent, "02 / 03");
});
