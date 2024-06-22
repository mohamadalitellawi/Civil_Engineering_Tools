import json
import shapely
from shapely import (
    Point, 
    MultiPoint, 
    Polygon, 
    MultiPolygon, 
    LineString, 
    MultiLineString,
    GeometryCollection
)
from dataclasses import dataclass
from typing import Optional
import numpy as np
import more_itertools


@dataclass
class ColumnArea:
    column_outline: Polygon
    trib_area: Polygon
    occupancies: dict
    column_load: Optional[np.ndarray] = None
    def get_combined_load(self, load_factors:np.ndarray = np.zeros(3), scale_factor:float = 1.0):
        if self.column_load.any():
            return (self.column_load * load_factors).sum() * scale_factor
        else:
            return 0

# assumed unit is mm for length and area, KPA for area loading, KN for force

def get_column_area_loads(floor_data:dict, occupancy_loading:dict, max_seg_length:float = 300) -> list[ColumnArea]:
    '''
    return list of columnarea class

    floor_data: json or dict for slab outline, openings, walls, columns, occupancy load areas
    occupancy_loading: json or dict for occupancy categories and uniform area load values as per load cases
    max_seg_length: for walls only
    '''
    slab_outline = floor_data.get('slab_outline', [])
    slab_openings = floor_data.get('slab_openings',[])
    columns = floor_data.get('columns',[])
    walls = floor_data.get('walls',[])
    load_light = floor_data.get('light_occupancy',[])
    load_heavy = floor_data.get('heavy_occupancy',[])

    slab_outline = Polygon(slab_outline)
    load_light = Polygon(load_light)
    load_heavy = Polygon(load_heavy)
    slab_openings = MultiPolygon([Polygon(outline) for outline in slab_openings])
    columns = MultiPolygon([Polygon(outline) for outline in columns])
    walls = MultiPolygon([Polygon(outline) for outline in walls])

    slab = Polygon(
        shell = slab_outline.exterior.coords,
        holes = [opening.exterior.coords for opening in slab_openings.geoms]
    )

    # Make sure the first/last point is not duplicated in the list
    column_points = [list(column.exterior.coords)[:-1] for column in columns.geoms]

    # Break up wall in to smaller segments according to a maximum segment length
    max_seg_length

    segmented_walls = [
        Polygon(shapely.segmentize(wall.exterior, max_seg_length))
        for wall in walls.geoms
    ]
    wall_points = [list(wall.exterior.coords)[:-1] for wall in segmented_walls]

    grouped_points = column_points + wall_points
    flattened_points = list(more_itertools.flatten(grouped_points))
    voronoi_source = MultiPoint(flattened_points)
    v_polys = shapely.voronoi_polygons(voronoi_source)

    # Get the clipped voronoi regions
    trib_components = [slab & v_poly for v_poly in v_polys.geoms]

    # Reorder trib components to match order of source points
    reordered_components = []
    for point in flattened_points: # Iterate by points to prioritize point order
        for poly in trib_components:
            if poly.contains(Point(point)) or poly.touches(Point(point)):
                reordered_components.append(poly)
    if len(reordered_components) != len(flattened_points):
        return
    
    # Group trib components by their source geometry
    all_polygons = list(columns.geoms) + segmented_walls

    poly_lookup = {}
    for idx, point_group in enumerate(grouped_points):
        for point in point_group:
            poly_lookup.update({point: all_polygons[idx]})

    trib_lookup = {}
    for idx, trib_component in enumerate(reordered_components):
        corresponding_point = flattened_points[idx]
        corresponding_polygon = poly_lookup[corresponding_point]
        trib_component_list = trib_lookup.get(corresponding_polygon, [])
        trib_component_list.append(trib_component)
        trib_lookup[corresponding_polygon] = trib_component_list

    trib_area_lookup = {}
    for polygon, trib_components in trib_lookup.items():
        trib_area_lookup[polygon] = shapely.unary_union(trib_components)

    occupancy_areas = {"heavy_occupancy": load_heavy, "light_occupancy": load_light}
    column_areas_acc = []

    for column, trib_area in trib_area_lookup.items():
        column_area = ColumnArea(column, trib_area, {})
        for occupancy, area_load in occupancy_areas.items():
            intersection = trib_area & area_load
            if not intersection.is_empty:
                column_area.occupancies.update({occupancy: intersection.area / trib_area.area})
        column_areas_acc.append(column_area)

    num_load_cases = len(list(occupancy_loading.values())[0])

    occupancy_vector = {occupancy: np.array(list(loads.values())) for occupancy, loads in occupancy_loading.items()}

    for column_area in column_areas_acc:
        total_load = np.zeros(num_load_cases)
        for occupancy, ratio in column_area.occupancies.items():
            total_load = total_load + ratio * occupancy_vector[occupancy] * column_area.trib_area.area / 1e6
        column_area.column_load = np.array(total_load)
    
    return column_areas_acc