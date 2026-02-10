# ---- Load libraries ----
library(readr)
library(ggplot2)
library(dplyr)
library(stringr)
library(tidyr)

# ---- Load data ----
data <- read_csv("results.csv", show_col_types = FALSE)

cat("Rows before filtering:", nrow(data), "\n")

# ---- Remove rows containing Timeout ----
data <- data[
  rowSums(sapply(data, function(col)
    grepl("Timeout", col, ignore.case = TRUE) %in% TRUE
  )) == 0,
]

cat("Rows after Timeout filtering:", nrow(data), "\n")

data <- data %>%
  mutate(
    Configurations = as.character(Configurations),
    Configurations = ifelse(Configurations == "Inf", Inf, Configurations),
    Configurations = as.numeric(Configurations)
  )

#---- Convert numeric columns safely ----
data <- data %>%
  mutate(
    Features = parse_number(as.character(Features)),
    Constraints = parse_number(as.character(Constraints)),
    `BDD Nodes` = parse_number(as.character(`BDD Nodes`)),
    Configurations = parse_number(as.character(Configurations))
  )

# ---- Remove rows with NA after conversion ----
data <- data %>%
  drop_na(Features, Constraints, `BDD Nodes`, Configurations)

cat("Rows after NA removal:", nrow(data), "\n")

# ------------------------------------------------------------
# Figure 1: Features vs BDD Nodes
# ------------------------------------------------------------
fig1 <- ggplot(data, aes(x = Features, y = `BDD Nodes`)) +
  geom_point() +
  theme_minimal()

fig1
ggsave("features_vs_bdd_nodes.png", fig1, width = 6, height = 4, dpi = 300)

# ------------------------------------------------------------
# Figure 2: Constraints vs BDD Nodes
# ------------------------------------------------------------
fig2 <- ggplot(data, aes(x = Constraints, y = `BDD Nodes`)) +
  geom_point() +
  theme_minimal()

fig2
ggsave("constraints_vs_bdd_nodes.png", fig2, width = 6, height = 4, dpi = 300)

# ------------------------------------------------------------
# Figure 3: BDD Nodes vs Configurations
# ------------------------------------------------------------
fig3 <- ggplot(data, aes(x = `BDD Nodes`, y = Configurations)) +
  geom_point() +
  scale_y_log10() +
  theme_minimal()

fig3
ggsave("bdd_nodes_vs_configurations.png", fig3, width = 6, height = 4, dpi = 300)
