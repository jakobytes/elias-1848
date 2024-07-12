import argparse
import pandas as pd
import geopandas as gpd
import shapely


def fill_holes(geometry, max_area=0):
    if type(geometry) == shapely.geometry.multipolygon.MultiPolygon:
        polygons = [fill_holes(p, max_area) for p in geometry.geoms]
        return shapely.geometry.multipolygon.MultiPolygon(polygons)
    holes = [shapely.geometry.Polygon(i) for i in geometry.interiors]
    for h in holes:
        if h.area <= max_area:
            geometry = geometry.union(h)
    return geometry


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Compute county polygons from parish polygons and '
                    'parish-to-county mappings.')
    parser.add_argument(
        '--areas-file', metavar='FILE', required=True,
        help='The parish polygons file (GeJSON).')
    parser.add_argument(
        '--places-file', metavar='FILE', required=True,
        help='The place list (CSV).')
    parser.add_argument(
        '--polygon-to-place-file', metavar='FILE', required=True,
        help='The place-to-polygon mapping list (CSV).')
    parser.add_argument(
        '-G', '--grid-size', metavar='SIZE', default=0.00001, type=float,
        help='Grid size for unary_union.')
    parser.add_argument(
        '-H', '--fill-hole-area', metavar='AREA', default=0.0, type=float,
        help='Fill holes in polygons smaller than AREA.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    areas = gpd.read_file(args.areas_file)
    places = pd.read_csv(args.places_file)
    poly_place = pd.read_csv(args.polygon_to_place_file)

    # join the tables and merge parish polygons to county polygons
    counties = (
        areas.merge(poly_place, left_on = 'id', right_on = 'polygon_id')
            .merge(places)
            .merge(places, left_on = 'place_parent_id', right_on = 'place_id')
            [['place_id_x', 'place_id_y', 'place_name_y',
              'parish_language', 'geometry']]
            .rename(columns = { 'place_id_y': 'place_id',
                                'place_name_y': 'county_name' })
            .groupby('place_id')
            .apply(lambda x: gpd.GeoDataFrame({
                'county_name': x['county_name'].iloc[:1],
                'parish_place_ids': [list(x['place_id_x'])],
                'county_language': [x['parish_language'].mode()[0]] \
                    if not x['parish_language'].mode().empty else [None],
                'geometry': [fill_holes(
                    shapely.unary_union(x['geometry'].to_list(),
                                        grid_size=args.grid_size),
                    max_area = args.fill_hole_area)],
                },
                crs=areas.crs))
            .reset_index()
           [['place_id', 'parish_place_ids', 'county_name',
             'county_language', 'geometry']]
    )
    counties = counties.assign(id = areas['id'].max() + counties.index + 1)
    
    print(counties.to_json())

