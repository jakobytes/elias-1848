raw_dir = data/raw
work_dir = data/work
DATA_DIR := $(if $(DATA_DIR),$(DATA_DIR),data/output)

python = python3

preprocess: skvr erab jr kr

skvr: \
  $(work_dir)/skvr/collectors.csv \
  $(work_dir)/skvr/verses.csv \
  $(work_dir)/skvr/word_occ.csv

erab: \
  $(work_dir)/erab/verses.csv \
  $(work_dir)/erab/word_occ.csv

jr: \
  $(work_dir)/jr/verses.csv \
  $(work_dir)/jr/word_occ.csv

kr: \
  $(work_dir)/kr/collectors.csv \
  $(work_dir)/kr/verses.csv \
  $(work_dir)/kr/places.csv \
  $(work_dir)/kr/poem_collector.csv \
  $(work_dir)/kr/poem_year.csv \
  $(work_dir)/kr/poem_place.csv \
  $(work_dir)/kr/poem_types.csv \
  $(work_dir)/kr/types.csv \
  $(work_dir)/kr/word_occ.csv

###################################################################
# PREPROCESSING
###################################################################

$(work_dir)/skvr/verses.csv:
	mkdir -p $(work_dir)/skvr
	$(python) code/convert_skvr.py \
      -d $(work_dir)/skvr \
      --places-file $(raw_dir)/skvr/places.csv \
      --xml-types-file $(raw_dir)/skvr/tyyppiluettelo.xml \
      --json-types-file $(raw_dir)/skvr/themetree.json \
      --poem-types-file $(raw_dir)/skvr/viitteet_180221.txt \
	  $(raw_dir)/skvr/skvr_*.xml

$(work_dir)/erab/verses.csv:
	mkdir -p $(work_dir)/erab
	$(python) code/convert_erab.py \
	  -i data/raw/erab/csv -p erab_ -d $(work_dir)/erab  \
	  $(raw_dir)/erab/xml/*.xml

$(work_dir)/jr/verses.csv:
	mkdir -p $(work_dir)/jr
	$(python) code/convert_jr.py \
	  -d $(work_dir)/jr $(raw_dir)/jr/*.xml

# For now, let all tables depend on the verses table, as they are processed
# together. In the future, we might break up the preprocessing scripts so
# that some parts are preprocessed independently of others.

$(work_dir)/skvr/meta.csv:           $(work_dir)/skvr/verses.csv
$(work_dir)/skvr/places.csv:         $(work_dir)/skvr/verses.csv
$(work_dir)/skvr/poem_types.csv:     $(work_dir)/skvr/verses.csv
$(work_dir)/skvr/raw_meta.csv:       $(work_dir)/skvr/verses.csv
$(work_dir)/skvr/refs.csv:           $(work_dir)/skvr/verses.csv
$(work_dir)/skvr/types.csv:          $(work_dir)/skvr/verses.csv
$(work_dir)/skvr/xmltypes.csv:       $(work_dir)/skvr/verses.csv

$(work_dir)/skvr/collectors.csv: $(raw_dir)/skvr/collectors.csv
	mkdir -p $(work_dir)/skvr
	sed '1s/.*/collector_id,collector_name/;' $< > $@

$(work_dir)/skvr/poem_place.csv: $(work_dir)/skvr/meta.csv
	csvcut -c poem_id,place_id $< > $@

$(work_dir)/skvr/poem_collector.csv: $(work_dir)/skvr/meta.csv
	csvcut -c poem_id,collector_id $< > $@

$(work_dir)/skvr/poem_year.csv: $(work_dir)/skvr/meta.csv
	csvcut -c poem_id,year $< > $@

$(work_dir)/erab/collectors.csv:     $(work_dir)/erab/verses.csv
$(work_dir)/erab/genres.csv:         $(work_dir)/erab/verses.csv
$(work_dir)/erab/places.csv:         $(work_dir)/erab/verses.csv
$(work_dir)/erab/poem_collector.csv: $(work_dir)/erab/verses.csv
$(work_dir)/erab/poem_place.csv:     $(work_dir)/erab/verses.csv
$(work_dir)/erab/poem_types.csv:     $(work_dir)/erab/verses.csv
$(work_dir)/erab/poem_year.csv:      $(work_dir)/erab/verses.csv
$(work_dir)/erab/raw_meta.csv:       $(work_dir)/erab/verses.csv
$(work_dir)/erab/refs.csv:           $(work_dir)/erab/verses.csv
$(work_dir)/erab/types.csv:          $(work_dir)/erab/verses.csv

$(work_dir)/jr/raw_meta.csv:       $(work_dir)/jr/verses.csv
$(work_dir)/jr/refs.csv:           $(work_dir)/jr/verses.csv
$(work_dir)/jr/poem_place.csv:     $(work_dir)/jr/verses.csv
$(work_dir)/jr/poem_collector.csv: $(work_dir)/jr/verses.csv
$(work_dir)/jr/poem_year.csv:      $(work_dir)/jr/verses.csv

$(work_dir)/kr/verses.csv:
	mkdir -p $(work_dir)/kr
	$(python) code/convert_skvr.py -p '' \
      -d $(work_dir)/kr \
	  $(raw_dir)/kr/*.xml $(raw_dir)/kr/kanteletar/*.xml

$(work_dir)/kr/meta.csv:     $(work_dir)/kr/verses.csv
$(work_dir)/kr/raw_meta.csv: $(work_dir)/kr/verses.csv

$(work_dir)/kr/collectors.csv: $(raw_dir)/kr/collectors.csv
	mkdir -p $(work_dir)/kr
	cp $< $@

$(work_dir)/kr/poem_place.csv: $(work_dir)/kr/meta.csv
	csvcut -c poem_id,place_id $< | csvgrep -c place_id -r '^.+$$' > $@

$(work_dir)/kr/poem_collector.csv: $(work_dir)/kr/meta.csv
	csvcut -c poem_id,collector_id $< | csvgrep -c collector_id -r '^.+$$' > $@

$(work_dir)/kr/poem_types.csv: $(raw_dir)/kr/kanteletar/poem_category.csv
	mkdir -p $(work_dir)/kr
	cp $< $@

$(work_dir)/kr/poem_year.csv: $(work_dir)/kr/meta.csv
	csvcut -c poem_id,year $< | csvgrep -c year -r '^.+$$' > $@

$(work_dir)/kr/places.csv: $(raw_dir)/kr/places.csv
	mkdir -p $(work_dir)/kr
	cp $< $@

$(work_dir)/kr/types.csv: $(raw_dir)/kr/kanteletar/categories.csv
	mkdir -p $(work_dir)/kr
	cp $< $@

# Verse cleaning
$(work_dir)/%/verses_cl.csv: $(work_dir)/%/verses.csv
	csvgrep -c verse_type -r "V" $< \
	| csvcut -c poem_id,pos,text \
	| $(python) code/clean_verses.py -c text > $@

# Tokenization of the cleaned verses table: just split on word boundaries.
$(work_dir)/%/word_occ.csv: $(work_dir)/%/verses_cl.csv
	awk -F, 'NR == 1 { print "poem_id,pos,word_pos,text"; }'\
	' NR > 1 { gsub("_+", "_", $$3);'\
	'         split($$3, a, "_");'\
	'         for (i in a) { print $$1","$$2","i","a[i]; } }'\
	  $< > $@

###################################################################
# COMBINED TABLES
###################################################################

# In the standard case, the combined tables are just concatenations
# of the tables for the individual subcorpora (using csvstack).
# Exceptions to this rule should be very rare and small.

# TODO provide for the possibility that the private repositories are empty
# (making a version using just the public data)

combined: \
  $(DATA_DIR)/areas.geojson \
  $(DATA_DIR)/collectors.csv \
  $(DATA_DIR)/counties.geojson \
  $(DATA_DIR)/places.csv \
  $(DATA_DIR)/poem_collector.csv \
  $(DATA_DIR)/poem_place.csv \
  $(DATA_DIR)/poem_year.csv \
  $(DATA_DIR)/poem_types.csv \
  $(DATA_DIR)/polygon_to_place.csv \
  $(DATA_DIR)/raw_meta.csv \
  $(DATA_DIR)/types.csv \
  $(DATA_DIR)/verses.csv \
  $(DATA_DIR)/verses_cl.csv \
  $(DATA_DIR)/word_occ.csv

$(DATA_DIR)/areas.geojson: $(raw_dir)/areas.geojson
	cp $< $@

$(DATA_DIR)/collectors.csv: \
  $(work_dir)/skvr/collectors.csv \
  $(work_dir)/erab/collectors.csv \
  $(work_dir)/kr/collectors.csv
	csvstack $^ > $@

$(DATA_DIR)/counties.geojson: \
  $(raw_dir)/areas.geojson \
  $(raw_dir)/polygon_to_place.csv \
  $(DATA_DIR)/places.csv
	$(python) code/compute_county_polygons.py -G 10 -H 1000000 \
	  --areas-file $(raw_dir)/areas.geojson \
	  --polygon-to-place-file $(raw_dir)/polygon_to_place.csv \
	  --places-file $(DATA_DIR)/places.csv > $@

$(DATA_DIR)/places.csv: \
  $(work_dir)/skvr/places.csv \
  $(work_dir)/erab/places.csv \
  $(work_dir)/kr/places.csv
	csvstack $^ > $@

$(DATA_DIR)/poem_collector.csv: \
  $(work_dir)/skvr/poem_collector.csv \
  $(work_dir)/erab/poem_collector.csv \
  $(work_dir)/jr/poem_collector.csv \
  $(work_dir)/kr/poem_collector.csv
	csvstack $^ > $@

$(DATA_DIR)/poem_place.csv: \
  $(work_dir)/skvr/poem_place.csv \
  $(work_dir)/erab/poem_place.csv \
  $(work_dir)/jr/poem_place.csv \
  $(work_dir)/kr/poem_place.csv
	csvstack $^ > $@

$(DATA_DIR)/poem_types.csv: \
  $(work_dir)/skvr/poem_types.csv \
  $(work_dir)/erab/poem_types.csv \
  $(work_dir)/kr/poem_types.csv
	csvstack $^ > $@

$(DATA_DIR)/poem_year.csv: \
  $(work_dir)/skvr/poem_year.csv \
  $(work_dir)/erab/poem_year.csv \
  $(work_dir)/jr/poem_year.csv \
  $(work_dir)/kr/poem_year.csv
	csvstack $^ > $@

$(DATA_DIR)/polygon_to_place.csv: \
  $(raw_dir)/polygon_to_place.csv \
  $(DATA_DIR)/counties.geojson
	cp $< $@
	jq -r '.features[] | [.properties.id, .properties.place_id ] | @tsv'\
	    $(DATA_DIR)/counties.geojson \
	| sed 's/$$/\t1/' | csvformat -t -U 3 >> $@
	jq -r '.features[] | [.properties.id,'\
	'                    ( .properties.parish_place_ids | join(",") ) ] | @tsv'\
	    $(DATA_DIR)/counties.geojson \
	| awk '{ gsub(",", "\n"$$1",", $$2); print $$1","$$2; }' \
	| sed 's/$$/,0/' >> $@

$(DATA_DIR)/raw_meta.csv: \
  $(work_dir)/skvr/raw_meta.csv \
  $(work_dir)/erab/raw_meta.csv \
  $(work_dir)/jr/raw_meta.csv \
  $(work_dir)/kr/raw_meta.csv
	csvstack $^ > $@

$(DATA_DIR)/refs.csv: \
  $(work_dir)/skvr/refs.csv \
  $(work_dir)/erab/refs.csv \
  $(work_dir)/jr/refs.csv
	csvstack $^ > $@

# Here we only keep columns that are present in all subcorpora.
# (`type_comparison` is only present in SKVR)
$(DATA_DIR)/types.csv: \
  $(work_dir)/skvr/types.csv \
  $(work_dir)/erab/types.csv \
  $(work_dir)/kr/types.csv
	csvstack $^ \
	| csvcut -c type_id,type_name,type_description,type_parent_id > $@
	python3 code/add_type_links.py $@ -t 0.7

$(DATA_DIR)/verses.csv: \
  $(work_dir)/skvr/verses.csv \
  $(work_dir)/erab/verses.csv \
  $(work_dir)/jr/verses.csv \
  $(work_dir)/kr/verses.csv
	csvstack $^ > $@

$(DATA_DIR)/verses_cl.csv: \
  $(work_dir)/skvr/verses_cl.csv \
  $(work_dir)/erab/verses_cl.csv \
  $(work_dir)/jr/verses_cl.csv \
  $(work_dir)/kr/verses_cl.csv
	csvstack $^ > $@

$(DATA_DIR)/word_occ.csv: \
  $(work_dir)/skvr/word_occ.csv \
  $(work_dir)/erab/word_occ.csv \
  $(work_dir)/jr/word_occ.csv \
  $(work_dir)/kr/word_occ.csv
	csvstack $^ > $@

###################################################################
# VERSE SIMILARITY AND CLUSTERING
###################################################################

$(work_dir)/verse_sim/verses_cl.list.txt: $(DATA_DIR)/verses_cl.csv
	mkdir -p $(work_dir)/verse_sim
	csvcut -c text $< | tail -n +2 | sort -u > $@

$(DATA_DIR)/v_sim.tsv: $(work_dir)/verse_sim/verses_cl.list.txt
	shortsim-ngrcos -t 0.75 -g -p -d 450 < $< > $@

$(work_dir)/verses_sim/v_clust.default.tsv: \
  $(work_dir)/verses_sim/verses_cl.list.txt \
  $(DATA_DIR)/v_sim.tsv
	echo \
	| cat $(work_dir)/verses_sim/verses_cl.list.txt - $(DATA_DIR)/v_sim.tsv \
	| shortsim-cluster -t 0.8 > $@

###################################################################
# POEMS SIMILARITY AND CLUSTERING
###################################################################

# TODO