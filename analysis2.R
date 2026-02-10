# Instalación de librerías si no las tienes:
# install.packages(c("ggplot2", "dplyr", "tidyr", "patchwork", "scales"))

library(ggplot2)
library(dplyr)
library(tidyr)
library(patchwork)
library(scales)

# 1. Cargar el dataset (sustituye 'results.csv' por tu ruta)
data <- read_csv("results.csv", show_col_types = FALSE)

# 2. Limpieza de datos
# Convertimos a numérico. Las celdas con "timeout" se convertirán en NA automáticamente
data <- data[
  rowSums(sapply(data, function(col)
    grepl("Timeout", col, ignore.case = TRUE) %in% TRUE
  )) == 0,
]

cat("Rows after Timeout filtering:", nrow(data), "\n")

df_clean <- data %>%
  mutate(
    Configurations = as.character(Configurations),
    Configurations = ifelse(Configurations == "Inf", Inf, Configurations),
    Configurations = as.numeric(Configurations)
  )


# --- GRÁFICA 1: Features vs Configuraciones (Escala Logarítmica) ---
p1 <- ggplot(df_clean, aes(x = Features, y = Configurations)) +
  geom_point(alpha = 0.6, color = "steelblue") +
  scale_y_log10(labels = trans_format("log10", math_format(10^.x))) +
  labs(title = "Configuration Space",
       subtitle = "Features vs Configurations (Log10)",
       x = "Features", y = "Configurations") +
  theme_minimal()

# --- GRÁFICA 2: Features vs Cláusulas (Complejidad Lógica) ---
p2 <- ggplot(df_clean, aes(x = Features, y = Clauses)) +
  geom_smooth(method = "lm", color = "darkred", se = TRUE) +
  geom_point(alpha = 0.5) +
  labs(title = "Logic representation",
       subtitle = "Features vs Clauses",
       x = "Features", y = "Clauses") +
  theme_minimal()

# --- GRÁFICA 3: Relación Variables vs Cláusulas ---
p3 <- ggplot(df_clean, aes(x = Variables, y = Clauses, size = Constraints)) +
  geom_point(alpha = 0.4, color = "darkgreen") +
  labs(title = "Logic structure",
       subtitle = "Variables vs Cláusulas (size = Constraints)",
       x = "Variables", y = "Clauses") +
  theme_minimal() +
  theme(legend.position = "bottom")

# --- GRÁFICA 4: Nodos BDD vs Features ---
p4 <- ggplot(df_clean, aes(x = Features, y = Nodes)) +
  geom_point(color = "purple", alpha = 0.6) +
  geom_density_2d(color = "black", alpha = 0.3) +
  labs(title = "BDD representation",
       subtitle = "Features vs BDD Nodes",
       x = "Features", y = "BDD Nodes") +
  theme_minimal()

# Unir todas las gráficas en un solo panel
layout <- (p1 + p2) / (p3 + p4)
layout
#layout + plot_annotation(title = "Análisis de Feature Models y sus Transformaciones",
 #                        caption = "Nota: Se han excluido filas con Timeout")