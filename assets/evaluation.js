/* Independent evaluation: no network calls, persistence, analytics or automatic submission. */
(() => {
  "use strict";
  const tasks = {
    intro: ["Find one AI-related initiative in the registry. Identify a supporting source. Explain what that source establishes and what it does not establish."],
    specialist: [
      "Find an AI-related claim in the registry. Trace it to supporting evidence and describe the source and its recorded classification.",
      "Find an official target. Investigate whether the available evidence establishes that the target was achieved, and describe any uncertainty.",
      "Find an open evidence gap. Explain what additional evidence would be needed to resolve the question."
    ]
  };
  const $ = (id) => document.getElementById(id);
  const form = $("eval-form");
  const modes = [...document.querySelectorAll("[data-mode]")];
  const state = {mode: "intro", index: 0, responses: {intro: [], specialist: []}};
  const fields = ["finding", "source", "limits"];
  const selectedDifficulty = () => form.querySelector('input[name="difficulty"]:checked');
  function capture() {
    return {finding: $("finding").value.trim(), source: $("source").value.trim(),
      limits: $("limits").value.trim(), difficulty: selectedDifficulty()?.value || "Not answered"};
  }
  function save() { state.responses[state.mode][state.index] = capture(); }
  function restore() {
    const answer = state.responses[state.mode][state.index] || {};
    fields.forEach(id => { $(id).value = answer[id] || ""; });
    form.querySelectorAll('input[name="difficulty"]').forEach(input => {
      input.checked = input.value === answer.difficulty;
    });
  }
  function render() {
    modes.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.mode === state.mode)));
    $("eval-progress").textContent = (state.mode === "intro" ? "Introductory" : "Specialist") +
      " · Task " + (state.index + 1) + " of " + tasks[state.mode].length;
    $("eval-prompt").textContent = tasks[state.mode][state.index];
    $("eval-next").hidden = state.index >= tasks[state.mode].length - 1;
    $("eval-prev").hidden = state.index === 0;
    restore();
  }
  modes.forEach(button => button.addEventListener("click", () => {
    save(); state.mode = button.dataset.mode; state.index = 0; render();
    $("eval-status").textContent = "Evaluation type changed. Draft answers remain in this tab only.";
  }));
  $("eval-next").addEventListener("click", () => {
    save();
    if (state.index < tasks[state.mode].length - 1) {
      state.index += 1; render(); $("eval-task").focus();
      $("eval-status").textContent = "Draft task saved in this tab only.";
    }
  });
  $("eval-prev").addEventListener("click", () => {
    save();
    if (state.index > 0) {
      state.index -= 1; render(); $("eval-task").focus();
      $("eval-status").textContent = "Draft task saved. Returned to the previous task.";
    }
  });
  $("eval-copy").addEventListener("click", () => {
    save();
    const name = state.mode === "intro" ? "Introductory" : "Specialist";
    const report = ["TheMoroccoAI — Independent Research Evaluation", "Evaluation: " + name,
      "Voluntary participant observations; not independently validated.", ""];
    tasks[state.mode].forEach((prompt, i) => {
      const a = state.responses[state.mode][i] || {};
      report.push("Task " + (i + 1) + ": " + prompt,
        "Finding: " + (a.finding || "[Not answered]"),
        "Evidence: " + (a.source || "[Not answered]"),
        "Limitations: " + (a.limits || "[Not answered]"),
        "Difficulty: " + (a.difficulty || "Not answered"), "");
    });
    $("eval-report").value = report.join("\n");
    $("eval-status").textContent = "Report prepared locally. Select and copy it manually; nothing has been submitted.";
    $("eval-report").focus();
    $("eval-report").select();
  });
  $("eval-clear").addEventListener("click", (event) => {
    event.preventDefault();
    state.responses = {intro: [], specialist: []}; state.index = 0;
    fields.forEach(id => { $(id).value = ""; });
    $("eval-report").value = ""; render();
    $("eval-status").textContent = "Draft responses and report cleared from this page.";
  });
  render();
})();