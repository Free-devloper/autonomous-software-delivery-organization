const [milestone, task] = process.argv.slice(2);

console.error(
  `${task ?? "This task"} is intentionally unavailable until milestone ${milestone ?? "its owning milestone"} is approved and implemented.`,
);
process.exit(2);
