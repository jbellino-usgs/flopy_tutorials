import os
import arcpy
import numpy as np
import copy

arcpy.CheckOutExtension('Spatial')
arcpy.env.overwriteOutput = True


def grid_to_array(grid, nrow, ncol, row_col_field_names, val_field_name):
    """
    Returns an array of shape (nrow, ncol) from a polygon grid of the same shape.
    Grid must have row/col values specified.
    vars:
         grid: name of grid feature class/layer; str
         nrow: number of rows; int
         ncol: number of columns; int
         row_col_field_names: names of fields containing row/col values for each cell; list, tuple
         val_field_name: name of field containing values of interest; same as row_col_field_names
    """
    if isinstance(row_col_field_names, tuple):
        row_col_field_names = list(row_col_field_names)
    cols = copy.deepcopy(row_col_field_names)
    cols.append(val_field_name)
    a = arcpy.da.TableToNumPyArray(grid, cols, skip_nulls=False)

    # Convert to recarray
    a_1 = np.rec.fromrecords(a.tolist(), names=['row', 'col', 'val'])
    a_1.sort(order=['row', 'col'])
    b = np.reshape(a_1.val, (nrow, ncol))
    return b


def import_surface(surface, grid, nrow, ncol, zstat_field=None, join_field='cell_id',
                   row_col_fields=['row', 'col'], statistic='MEAN', fill_value=None,
                   cellsize=1000.):
    """
    References raster surface to model grid and returns an array of shape (nrow, ncol).
    :param surface: the raster surface to be sampled; raster
    :param grid: the vector grid upon which the raster will be summarized; feature class
    :param nrow: number of rows in the grid; int
    :param ncol: number of columns in the grid; int
    :param zstat_field: field in the grid that defines the zones; str
    :param join_field: field in the resulting features to be used for the join; str
    :param row_col_fields: names of the fields containing row and column numbers; list
    :param statistic: alias of resulting zstat field(s) to use; str
    :param fill_value:
    :return:
    """
    arcpy.env.cellSize = cellsize
    # print('Cellsize:', arcpy.env.cellSize)
    statistic = statistic.upper()
    valid_stats = ['ALL', 'MEAN', 'MAJORITY', 'MAXIMUM', 'MEDIAN', 'MINIMUM', 'MINORITY',
                   'RANGE', 'STD', 'SUM', 'VARIETY', 'MIN_MAX', 'MEAN_STD', 'MIN_MAX_MEAN']
    assert statistic in valid_stats, 'Statistic is not valid.'
    if '_' in statistic:
        stat_field_names = statistic.split('_')
    elif statistic == 'ALL':
        stat_field_names = ['MEAN', 'MAJORITY', 'MAXIMUM', 'MEDIAN', 'MINIMUM', 'MINORITY',
                            'RANGE', 'STD', 'SUM', 'VARIETY']
    else:
        stat_field_names = statistic.upper()

    if join_field is None:
        join_field = arcpy.Describe(grid).OIDFieldName
    if zstat_field is None:
        zstat_field = join_field

    zstat = r'in_memory\{}'.format(os.path.basename(surface))
    arcpy.sa.ZonalStatisticsAsTable(in_zone_data=grid,
                                    zone_field=zstat_field,
                                    in_value_raster=surface,
                                    out_table=zstat,
                                    ignore_nodata='DATA',
                                    statistics_type=statistic)

    # Create feature layers and table views for joining
    grid_lyr = r'in_memory\grid_lyr'
    arcpy.MakeFeatureLayer_management(grid, grid_lyr)

    zstat_vwe = r'in_memory\zstat_vwe'
    arcpy.MakeTableView_management(zstat, zstat_vwe)

    # Join tables
    arcpy.AddJoin_management(grid_lyr, join_field, zstat_vwe, join_field, 'KEEP_ALL')

    # Write the grid features to a new featureclass
    zstat_grid = r'in_memory\zstat_grid'
    arcpy.CopyFeatures_management(grid_lyr, zstat_grid)

    # Update the row/col field names in case they were changed after the join
    for i, name in enumerate(row_col_fields):
        if name not in [f.name for f in arcpy.ListFields(zstat_grid)]:
            for (n, a) in [(f.name, f.aliasName) for f in arcpy.ListFields(zstat_grid)]:
                if name == a:
                    row_col_fields[i] = n

    # Ensure we point to the correct zstat field name in case of truncation
    arrays = list()
    for (name, alias) in [(f.name, f.aliasName) for f in arcpy.ListFields(zstat_grid)]:
        if alias in stat_field_names:
            # stat_field_aliases.append(name)
            a = grid_to_array(zstat_grid, nrow, ncol, row_col_fields, name)
            if fill_value is not None:
                a[np.isnan(a)] = fill_value
            arrays.append(a)

    # arrays = list()
    # for alias in stat_field_aliases:
    #     print(alias)
    #     a = grid_to_array(zstat_grid, nrow, ncol, row_col_fields, alias)
    #     if fill_value is not None:
    #         a[np.isnan(a)] = fill_value
    #     arrays.append(a)

    if len(arrays) == 1:
        return arrays[0]
    else:
        return arrays
