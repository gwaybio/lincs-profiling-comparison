suppressPackageStartupMessages(library(dplyr))

source("viz_themes.R")
source("plotting_functions.R")
source("data_functions.R")

updated_dose_rename <- dose_rename
names(updated_dose_rename) <- paste(format(round(as.integer(names(updated_dose_rename)), 1), nsmall = 1))
updated_dose_rename <- c(updated_dose_rename, "All" = "All")
updated_dose_rename

assay_update <- c("cell_painting" = "Cell Painting", "l1000" = "L1000")

# Load compound to moa map
file <- file.path(
    "..",
    "1.Data-exploration",
    "Consensus",
    "cell_painting",
    "moa_sizes_consensus_datasets",
    "cell_painting_moa_analytical_set_profiles.tsv.gz"
)

df_cols <- readr::cols(
  .default = readr::col_double(),
  Metadata_Plate_Map_Name = readr::col_character(),
  Metadata_cell_id = readr::col_character(),
  Metadata_broad_sample = readr::col_character(),
  Metadata_pert_well = readr::col_character(),
  Metadata_time_point = readr::col_character(),
  Metadata_moa = readr::col_character(),
  Metadata_target = readr::col_character(),
  broad_id = readr::col_character(),
  pert_iname = readr::col_character(),
  moa = readr::col_character()
)

cp_df <- readr::read_tsv(file, col_types = df_cols) %>%
    dplyr::select(broad_id, pert_iname, Metadata_dose_recode, moa, Metadata_target) %>%
    dplyr::distinct() %>%
    dplyr::arrange(pert_iname) %>%
    dplyr::rename(target = Metadata_target, dose = Metadata_dose_recode)

cp_df$pert_iname <- tolower(cp_df$pert_iname)
cp_df$moa <- tolower(cp_df$moa)

print(dim(cp_df))
head(cp_df)

# Load compound to moa map
file <- file.path(
    "..",
    "1.Data-exploration",
    "Consensus",
    "L1000",
    "moa_sizes_consensus_datasets",
    "L1000_moa_analytical_set_profiles.tsv.gz"
)

df_cols <- readr::cols(
  .default = readr::col_double(),
  sig_id = readr::col_character(),
  pert_id = readr::col_character(),
  pert_idose = readr::col_character(),
  pert_iname = readr::col_character(),
  moa = readr::col_character()
)

l1000_df <- readr::read_tsv(file, col_types = df_cols) %>%
    dplyr::full_join(
        cp_df,
        by = c(
            "pert_id" = "broad_id",
            "pert_iname" = "pert_iname",
            "moa" = "moa",
            "dose" = "dose"
        )
    ) %>%
    dplyr::select(pert_id, pert_iname, dose, moa, target) %>%
    dplyr::distinct() %>%
    dplyr::rename(broad_id = pert_id)

l1000_df$pert_iname <- tolower(l1000_df$pert_iname)
l1000_df$moa <- tolower(l1000_df$moa)

print(dim(l1000_df))
head(l1000_df)

map_df <- dplyr::bind_rows(cp_df, l1000_df) %>%
    dplyr::distinct()

map_df$dose <- dplyr::recode_factor(map_df$dose, !!!dose_rename)

map_df <- map_df %>%
    dplyr::arrange(pert_iname, dose)

# This is Supplementary Table 4
output_file <- file.path("results", "tableS1_compound_to_moa_target_map.tsv")
map_df %>% readr::write_tsv(output_file)

print(dim(map_df))
head(map_df, 7)

# Load median pairwise Spearman correlations
compound_cols <- readr::cols(
  compound = readr::col_character(),
  no_of_compounds = readr::col_double(),
  well = readr::col_character(),
  dose_recode = readr::col_double(),
  median_score = readr::col_double(),
  p_value = readr::col_double(),
  assay = readr::col_character(),
  normalization = readr::col_character(),
  category = readr::col_character(),
  pass_thresh = readr::col_logical(),
  neg_log_10_p_val = readr::col_double(),
  dose = readr::col_character()
)

# This is Supplementary Table 1
compound_df <- readr::read_tsv(file.path("results", "compound_scores.tsv"), col_types = compound_cols) %>%
    dplyr::select(compound, dose, no_of_compounds, well, median_score, p_value, assay) %>%
    dplyr::rename(
        no_of_replicates_per_compound = no_of_compounds,
        median_replicate_correlation = median_score
    )

# Output sup table 1
output_file <- file.path("results", "tableS2_compound_percent_replicating.tsv")
compound_df %>% readr::write_tsv(output_file)

print(dim(compound_df))
head(compound_df, 3)

# Load Signature Strength and MAS scores
ora_results_dir <- file.path("..", "5.Gene-analysis", "results")

ora_results_file <- file.path(ora_results_dir, "ora_compound_results.tsv")

ora_cols <- readr::cols(
    geneSet = readr::col_character(),
    description = readr::col_character(),
    link = readr::col_character(),
    size = readr::col_double(),
    overlap = readr::col_double(),
    expect = readr::col_double(),
    enrichmentRatio = readr::col_double(),
    pValue = readr::col_double(),
    FDR = readr::col_double(),
    overlapId = readr::col_character(),
    database = readr::col_character(),
    userId = readr::col_character(),
    compound = readr::col_character()
)

ora_df <- readr::read_tsv(ora_results_file, col_types = ora_cols) %>%
    dplyr::left_join(
        map_df %>%
            dplyr::select(broad_id, pert_iname, moa, target) %>%
            dplyr::distinct(),
        by = c("compound" = "pert_iname")
        )

# This is Supplementary Table 5
output_file <- file.path("results", "tableS3_overrepresentationanalysis.tsv")
ora_df %>% readr::write_tsv(output_file)

print(dim(ora_df))
head(ora_df, 3)

# Load MOA percent matching
moa_cols <- readr::cols(
  moa = readr::col_character(),
  no_of_replicates = readr::col_double(),
  dose = readr::col_character(),
  matching_score = readr::col_double(),
  assay = readr::col_character(),
  p_value = readr::col_double(),
  pass_thresh = readr::col_logical(),
  neg_log_10_p_val = readr::col_double()
)

moa_df <- readr::read_tsv(file.path("results", "moa_scores.tsv"), col_types = moa_cols) %>%
    dplyr::select(moa, dose, no_of_replicates, matching_score, p_value, assay) %>%
    dplyr::rename(
        no_of_compounds_per_moa = no_of_replicates,
        median_replicate_correlation = matching_score
    )

print(dim(moa_df))
head(moa_df, 3)

# Load MOA and target average precision
file <- file.path(
    "..",
    "1.Data-exploration",
    "results",
    "moa_target_precision.tsv.gz"
)

df_cols <- readr::cols(
  drug_impact = readr::col_character(),
  dose = readr::col_character(),
  avg_precision = readr::col_double(),
  impact_category = readr::col_character(),
  assay = readr::col_character(),
  dose_comparison = readr::col_character()
)

avg_precision_df <- readr::read_tsv(file, col_types = df_cols)

# Update dose and assay column
avg_precision_df$dose <- dplyr::recode_factor(avg_precision_df$dose, !!!updated_dose_rename)
avg_precision_df$assay <- dplyr::recode_factor(avg_precision_df$assay, !!!assay_update)

print(dim(avg_precision_df))
head(avg_precision_df, 3)

# Generate sup table 4
sup_table_4_df <- avg_precision_df %>%
    dplyr::filter(impact_category == "moa") %>%
    dplyr::inner_join(
        moa_df,
        by = c("drug_impact" = "moa", "dose" = "dose", "assay" = "assay")
    ) %>%
    dplyr::select(
        drug_impact,
        dose,
        assay,
        avg_precision,
        no_of_compounds_per_moa,
        median_replicate_correlation,
        p_value
    ) %>%
    dplyr::rename(
        p_value_percent_matching = p_value,
        moa = drug_impact
    ) %>%
    dplyr::arrange(moa)


output_file <- file.path("results", "tableS4_moa_metrics.tsv")
sup_table_4_df %>% readr::write_tsv(output_file)

head(sup_table_4_df)

file <- file.path(
    "..",
    "1.Data-exploration",
    "results",
    "gene_target_median_pairwise_correlations.tsv.gz"
)

target_cols <- readr::cols(
  target = readr::col_character(),
  dose = readr::col_character(),
  median_correlation = readr::col_double(),
  n_compounds = readr::col_double(),
  assay = readr::col_character()
)

target_cor_df <- readr::read_tsv(file, col_types = target_cols)

target_update_dose_rename <- c(dose_rename, "All" = "All")

target_cor_df$dose <- dplyr::recode_factor(target_cor_df$dose, !!!target_update_dose_rename)

print(dim(target_cor_df))
head(target_cor_df)

sup_table_5_df <- avg_precision_df %>%
    dplyr::filter(impact_category == "target") %>%
    dplyr::inner_join(
        target_cor_df,
        by = c("drug_impact" = "target", "dose" = "dose", "assay" = "assay")
    ) %>%
    dplyr::select(
        drug_impact,
        dose,
        assay,
        avg_precision,
        n_compounds,
        median_correlation,
    ) %>%
    dplyr::rename(
        target = drug_impact,
        no_of_compounds_per_target = n_compounds
    ) %>%
    dplyr::arrange(target, dose)

output_file <- file.path("results", "tableS5_target_metrics.tsv")
sup_table_5_df %>% readr::write_tsv(output_file)

print(dim(sup_table_5_df))
head(sup_table_5_df)

# Load average precision scores for all models and targets
metric_dir <- file.path("..", "2.MOA-prediction", "metrics")
ap_file <- file.path(metric_dir, "average_precision_full_results.tsv.gz")

ap_cols <- readr::cols(
  average_precision = readr::col_double(),
  target = readr::col_character(),
  assay = readr::col_character(),
  model = readr::col_character(),
  shuffle = readr::col_logical(),
  data_split = readr::col_character(),
  target_category = readr::col_character()
)

ap_df <- readr::read_tsv(ap_file, col_types = ap_cols)

ap_df$assay <- dplyr::recode(
    ap_df$assay, "cp" = "Cell_Painting", "L1000" = "L1000"
)

ap_df$model <- dplyr::recode(
    ap_df$model,
        "mlknn" = "KNN",
        "simplenn" = "Simple_NN",
        "resnet" = "ResNet",
        "1dcnn" = "1D_CNN",
        "tabnet" = "TabNet",
        "blend" = "Ensemble"
)

# This is Supplementary Table 6
output_file <- file.path("results", "tableS6_deeplearning_avgprecision.tsv.gz")
ap_df %>% readr::write_tsv(output_file)

print(dim(ap_df))
head(ap_df, 2)
