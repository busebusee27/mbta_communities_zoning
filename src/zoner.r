library(sf)
library(spdep)
library(bigDM)
library(redist)
library(dplyr)
library(jsonlite)


zone <- function(absolute_path, n_districts) {
    shp <- read_sf(absolute_path, layer = "community")

    # creating the population column
    shp$pop <- 1

    # mapping to the right CRS/reference
    shp <- shp %>%
        st_set_crs(26915) %>%
        st_transform(26915)

    # -----------------------------------------------
    # Step 1: Compute Initial Adjacency using poly2nb
    # -----------------------------------------------
    # Using a snap tolerance (here 0.001) can help connect nearly touching polygons.
    initial_nb <- poly2nb(shp, snap = 0.001)

    # -----------------------------------------------
    # Step 2: Use bigDM's connect_subgraphs to repair disconnected parts.
    # -----------------------------------------------
    # Provide the unique identifier column ("ID") so that bigDM can correctly handle unit matching.
    conn <- connect_subgraphs(carto = shp, ID.area = "LOC_ID", nb = initial_nb, plot = FALSE)
    adjusted_nb <- conn$nb # still a spdep "nb" object, 1-indexed with extra attributes

    # ---------------------------------------------------
    # Step 3: Convert adjusted_nb to a plain, 0-indexed list
    # ---------------------------------------------------
    # redist_map expects a simple list of integer vectors with 0-indexed values.
    adj_list <- lapply(unclass(adjusted_nb), function(neighbors) {
        if (length(neighbors) > 0) {
            as.integer(neighbors - 1)
        } else {
            integer(0)
        }
    })
    class(adj_list) <- "list" # Remove extra attributes

    # ----------------------------------------------------------------------------
    # Step 5: Enforce reciprocal (symmetric) neighbor relationships.
    # ----------------------------------------------------------------------------
    # Even if unit A lists unit B as a neighbor, redist_map expects that B’s list also includes A.
    for (i in seq_along(adj_list)) {
        for (j in adj_list[[i]]) {
            neighbor_idx <- j + 1 # Convert from 0-indexed to R's indexing.
            if (!((i - 1) %in% adj_list[[neighbor_idx]])) {
                adj_list[[neighbor_idx]] <- c(adj_list[[neighbor_idx]], i - 1)
            }
        }
    }

    # ADD CONSTRAINTS

    # ------------------------------------------------------------------
    # Step 6: Create and validate the redist_map Object
    # ------------------------------------------------------------------
    redist_map_obj <- redist_map(
        shp,
        ndists = n_districts, # Set the desired number of districts.
        pop_tol = 1, # Population tolerance; adjust as needed.
        total_pop = "pop", # Must match the population column name.
        adj = adj_list, # Provide the cleaned, 0-indexed adjacency list.
    )

    plans <- redist_smc(redist_map_obj, 100, compactness = 1, runs = 1, verbose = TRUE, ncores = 4)

    ret <- t(attributes(plans)$plans)

    zonings <- toJSON(ret)
    write(zonings, file="cached.json")

    ret
}
