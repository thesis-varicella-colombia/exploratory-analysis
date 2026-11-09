#!/usr/bin/env Rscript
# Export EpiEstim's parametric-SI result for a continuous weekly test block.
# Usage: Rscript scripts/compare_epiestim_reference.R INPUT.csv OUTPUT_PREFIX

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop("Usage: Rscript compare_epiestim_reference.R INPUT.csv OUTPUT_PREFIX")
}
suppressPackageStartupMessages(library(EpiEstim))
counts <- read.csv(args[1])$notifications
if (length(counts) < 5L || anyNA(counts) ||
    any(counts < 0) || any(counts != floor(counts))) {
  stop("Expected at least five nonnegative integer weekly counts")
}

fit <- EpiEstim::estimate_R(
  incid = as.integer(counts),
  method = "parametric_si",
  dt = 7L,
  dt_out = 14L,
  recon_opt = "naive",
  iter = 10L,
  config = EpiEstim::make_config(list(
    mean_si = 14.1, std_si = 2.4,
    mean_prior = 5, std_prior = 5
  ))
)
prefix <- args[2]
weights <- EpiEstim::discr_si(0:length(fit$I), 14.1, 2.4)
stopifnot(length(weights) == length(fit$si_distr),
          max(abs(weights - as.numeric(fit$si_distr))) < 1e-12)
write.csv(data.frame(day = seq_along(fit$I), reconstructed = fit$I),
          paste0(prefix, "_daily.csv"), row.names = FALSE)
write.csv(fit$R, paste0(prefix, "_posterior.csv"), row.names = FALSE)
write.csv(data.frame(lag = seq_along(weights) - 1L, weight = weights),
          paste0(prefix, "_weights.csv"), row.names = FALSE)
writeLines(c(
  paste("R:", R.version.string),
  paste("EpiEstim:", as.character(packageVersion("EpiEstim"))),
  paste("Weekly counts:", length(counts)),
  paste("dt: 7; dt_out: 14; recon_opt: naive; iter: 10"),
  paste("SI mean: 14.1; SI SD: 2.4; prior mean: 5; prior SD: 5")
), paste0(prefix, "_versions.txt"))
