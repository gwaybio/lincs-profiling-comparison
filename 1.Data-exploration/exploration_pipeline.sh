#!/bin/bash
#
# Run to reproduce the full pipeline `./exploration_pipeline.sh`
#
# Note: All files generated by the below notebooks are already included in this repository.
# For processing of an important file used below, see 6.paper_figures/figure2.ipynb

############################
# Step 1 - Align compound metadata between the two assays
############################
cd Profiles_level4
jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute align_MOA_L1000_CellPainting.ipynb

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/nbconverted *.ipynb

############################
# Step 2 - Analyzing level 4 profiles
############################
# Cell Painting
cd cell_painting
jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 1.cellpainting_calculate_cpd_median_score_spherized.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 2.cellpainting_calculate_SS_MAS.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 3.cellpainting_calculate_null_p_values.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 4.cellpainting_visualization.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 5.cellpainting_calculate_cpd_median_score_normalized.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 6.cellpainting_calculate_subsampled_replicatescores.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 7.cellpainting_calculate_subsampled_null_p_values.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 8.cellpainting_calculate_nonspherized_null_p_values.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 9.cellpainting-percent-replicating-subsampled-and-nonspherized.ipynb

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/nbconverted *.ipynb

# L1000
cd ../L1000
jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 1.L10000_calculate_cpd_median_score.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 2.L10000_calculate_SS_TAS.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 3.L10000_calculate_null_p_values.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 4.L10000_visualization.ipynb

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/nbconverted *.ipynb

# L1000 and Cell Painting comparison
cd ../L1000_cellpainting_comparison

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute L1000_CP_comparison_visualization.ipynb

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/nbconverted *.ipynb

# Analyze plate position effects
cd ../plate_position_effects
jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute gather-platemap-metadata.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute inspect-plate-position-effects.ipynb

# Uncomment to run diffusion analysis (takes days)
#bash diffusion.sh

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/nbconverted *.ipynb

############################
# Step 3 - Analyzing level 5 profiles (Consensus signatures)
############################
# Cell Painting
cd ../../Consensus/cell_painting
jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 1.cellpainting_moa_median_scores_calculation.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 2.cellpainting_null_p_values_calculation.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 3.cellpainting_visualization.ipynb

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/nbconverted *.ipynb

# L1000
cd ../L1000
jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 1.L1000_moa_median_scores_calculation.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 2.L1000_null_p_values_calculation.ipynb

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute 3.L1000_visualization.ipynb

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/nbconverted *.ipynb

# L1000 and Cell Painting comparison
cd ../L1000_cell_painting_comparison

jupyter nbconvert --to=html \
        --FilesWriter.build_directory=scripts/html \
        --ExecutePreprocessor.kernel_name=python3 \
        --ExecutePreprocessor.timeout=10000000 \
        --execute L1000_CP_comparison_visualization.ipynb

jupyter nbconvert --to=script --FilesWriter.build_directory=scripts/nbconverted *.ipynb
