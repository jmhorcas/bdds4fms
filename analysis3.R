# Librerías necesarias
library(readr)
library(ggplot2)
library(dplyr)
library(tidyr)
library(patchwork)
library(scales)

# 1. Cargar el dataset
data <- read_csv("results.csv", show_col_types = FALSE)

# 2. Limpieza de datos (Quitar Timeouts)
data <- data[
  rowSums(sapply(data, function(col)
    grepl("Timeout", col, ignore.case = TRUE) %in% TRUE
  )) == 0,
]

df_clean <- data %>%
  mutate(
    Configurations = as.numeric(as.character(Configurations))
  ) %>%
  filter(Features > 0, Clauses > 0, Variables > 0, Nodes > 0) # Filtrar ceros para evitar errores en log

# --- GRÁFICA 1: Features vs Configuraciones ---
p1 <- ggplot(df_clean, aes(x = Features, y = Configurations)) +
  geom_point(alpha = 0.4, color = "steelblue") +
  scale_x_log10(labels = label_log()) +
  scale_y_log10(labels = label_log()) +
  #annotation_logticks() + # Añade las marcas visuales de logaritmo
  labs(title = "Configuration Space",
       subtitle = "Features vs Configurations",
       x = "Features", y = "Configurations") +
  theme_minimal()

# --- GRÁFICA 2: Features vs Cláusulas ---
p2 <- ggplot(df_clean, aes(x = Features, y = Clauses)) +
  geom_point(alpha = 0.4, color = "darkgrey") +
  geom_smooth(method = "lm", color = "darkred", se = TRUE) +
  scale_x_log10(labels = label_log()) +
  scale_y_log10(labels = label_log()) +
  #annotation_logticks() +
  labs(title = "Logic representation",
       subtitle = "Features vs Clauses",
       x = "Features", y = "Clauses") +
  theme_minimal()

# --- GRÁFICA 3: Relación Variables vs Cláusulas ---
p3 <- ggplot(df_clean, aes(x = Variables, y = Clauses, size = Constraints)) +
  geom_point(alpha = 0.3, color = "darkgreen") +
  scale_x_log10(labels = label_log()) +
  scale_y_log10(labels = label_log()) +
  #annotation_logticks() +
  labs(title = "Logic structure",
       subtitle = "Variables vs Clauses (size = Constraints)",
       x = "Variables", y = "Clauses") +
  theme_minimal() +
  theme(legend.position = "bottom")

# --- GRÁFICA 4: Nodos BDD vs Features ---
p4 <- ggplot(df_clean, aes(x = Features, y = Nodes)) +
  geom_point(color = "purple", alpha = 0.4) +
  scale_x_log10(labels = label_log()) +
  scale_y_log10(labels = label_log()) +
  #annotation_logticks() +
  labs(title = "BDD representation",
       subtitle = "Features vs BDD Nodes",
       x = "Features", y = "BDD Nodes") +
  theme_minimal()

# Unir todas las gráficas
layout <- (p1 + p2) / (p3 + p4)
layout