# -*- coding: utf-8 -*-


# TAXIPP -- A French microsimulation model
# By: IPP <taxipp@ipp.eu>
#
# Copyright (C) 2012, 2013, 2014, 2015 IPP
# https://github.com/taxipp
#
# This file is part of TAXIPP.
#
# TAXIPP is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# TAXIPP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import copy
import logging
import numpy
import pandas
from py_expression_eval import Parser


log = logging.getLogger(__name__)


def look_up(df, entry_by_index, years = None):
    """
    Get the data corresponding to the parameters (code, institution, ressources, year, description) defined in the
    dictionnary "entry_by_index", from the DataFrame df containing the stacked Comptabilité Nationale data.
    Note that entering any entry_by_index containing a 'formula' key will give an empty Series.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by get_comptes_nationaux_data(year)
    entry_by_index : dictionnary
        A dictionnary with keys 'code', 'institution', 'ressources', 'year', 'description'.

    Example
    --------
    >>> from ipp_macro_series_parser.comptes_nationaux.cn_parser_main import get_comptes_nationaux_data
    >>> table2013 = get_comptes_nationaux_data(2013)
    >>> dico = {'code': 'B1g/PIB', 'institution': 'S1', 'ressources': False, 'year': None, 'description': 'PIB'}
    >>> df0 = look_up(table2013, dico)

    Returns a slice of get_comptes_nationaux_data(2013) containing only the gross product (PIB) of the whole economy
    (S1), for all years.
    """
    assert years is not None
    result = df.copy()
    result = result[df['year'].isin(years)].copy()
    for key, value in entry_by_index.items():
        if value is None:
            continue
        if key == 'drop':
            continue
        if key != 'description' and key != 'formula':
            try:
                query_expression = "{} == '{}'".format(key, value)
                result = df.query(query_expression)
            except KeyError, e:
                log.info('{} for {} is not available'.format(value, key))
                raise(e)
            if result.empty:
                log.info('Variable {} is not available'.format(value))
                result = pandas.DataFrame()
        elif key == 'description':
            result = result[df[key].str.contains(value)].copy()
        else:
            result = pandas.DataFrame()
    return result


def look_many(df, entry_by_index_list, years = None):
    """
    Get the multiple data corresponding to the parameters (the tuples (code, institution, ressources, year,
    description)) defined in the list of dictionnaries "entry_by_index_list", from the DataFrame df containing the
    stacked Comptabilité Nationale data.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by get_comptes_nationaux_data(year)
    entry_by_index_list : list of dictionnaries
        Dictionnaries should have keys 'code', 'institution', 'ressources', 'year', 'description', but not necesarily
        all of them.

    Example
    --------
    >>> table2013 = get_comptes_nationaux_data(2013)
    >>> my_list = [{'code': 'B1g/PIB', 'institution': 'S1', 'ressources': False},
        ...         {'code': 'B1n/PIN', 'institution': 'S1', 'ressources': False}]
    >>> df1 = look_many(table2013, my_list)

    Returns a slice of get_comptes_nationaux_data(2013) containing the gross product (PIB) and the net product (PIN) of
    the whole economy (S1), for all years.

    >>> my_list_2 = [{'code': None, 'institution': 'S1', 'ressources': False,
    ...             'description': 'PIB'},
    ...             {'code': None, 'institution': 'S1', 'ressources': False,
    ...             'description': 'PIN'}]
    >>> df2 = look_many(table2013, my_list_2, years = range(1990, 2014))

    Returns the same output, using a keyword from the description.
    """
    assert years is not None
    df_output = pandas.DataFrame()
    for entity in entry_by_index_list:
        df_inter = look_up(df, entity, years = years)
        df_output = pandas.concat([df_output, df_inter], axis = 0, ignore_index=False, verify_integrity=False)
    df_output = df_output.drop_duplicates()
    return df_output


def get_or_construct_value(df, variable_name, index_by_variable, years = None, fill_value = numpy.NaN):
    """
    Returns the DataFrame (1 column) of the value of economic variable(s) for years of interest.
    Years are set to the index of the DataFrame.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by get_comptes_nationaux_data(year)
    variable : string or dictionary
        Variable to get or to construct (by applying formula).
    index_by_variable : dictionary
        Contains all economic variables indexes and formula. Variables appearing in formula of variable should be
        listed in index_by_variable.
    years : list of integers
        Years of interest

    Example
    --------
    >>> table_cn = get_comptes_nationaux_data(2013)
    >>> index_by_variable = {
    ...    'Interets_verses_par_rdm': {
    ...         'code': 'D41',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': ''
    ...     },
    ...     'Dividendes_verses_par_rdm_D42': {
    ...         'code': 'D42',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': ''
    ...     },
    ...     'Dividendes_verses_par_rdm_D43': {
    ...         'code': 'D43',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': ''
    ...     },
    ...     'Revenus_propriete_verses_par_rdm': {
    ...         'code': 'D44',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': ''
    ...     },
    ...     'Interets_dividendes_verses_par_rdm': {
    ...         'code': None,
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': 'Interets et dividendes verses par RDM, nets',
    ...         'formula': 'Interets_verses_par_rdm + Dividendes_verses_par_rdm_D42 + Dividendes_verses_par_rdm_D43 + Revenus_propriete_verses_par_rdm'
    ...     }
    ... }
    >>> computed_variable_vector, computed_variable_formula = get_or_construct_value(
    ...     df, 'Interets_dividendes_nets_verses_par_rdm', index_by_variable
    ...     )

    Returns a tuple, where the first element is a DataFrame (with a single column) for years 1949 to 2013 of the value
    of the sum of the four variables, and the second element is the formula 'Interets_verses_par_rdm +
    Dividendes_verses_par_rdm_D42 + Dividendes_verses_par_rdm_D43 + Revenus_propriete_verses_par_rdm'
    """

    assert df is not None
    df = df.copy()

    assert years is not None

    assert variable_name is not None
    if index_by_variable is None:
        index_by_variable = {
            variable_name: {'code': variable_name}
            }
    variable = index_by_variable.get(variable_name, None)
    assert variable is not None, "{} not found".format(variable_name)

    formula = variable.get('formula')

    dico_value = dict()
    entry_df = look_up(df, variable, years)
    index = None

    if not entry_df.empty:
        entry_df = entry_df.set_index('year')
        result_data_frame = entry_df[['value']].copy()
        assert len(result_data_frame.columns) == 1
        result_data_frame.columns = [variable_name]
        try:
            result_data_frame = result_data_frame.reindex(index = years, copy = False)
        except:
            print result_data_frame
        final_formula = variable_name

    # For formulas that are not real formulas but that are actually a mapping
    elif not formula and entry_df.empty:
        result_data_frame = pandas.DataFrame()
        final_formula = ''

    else:
        # When formula is a list of dictionnaries with start and end years
        if isinstance(formula, list):
            result_data_frame = pandas.DataFrame()
            for individual_formula in formula:
                assert individual_formula['start'] or individual_formula['end']
                start = individual_formula.get('start', None)
                end = individual_formula.get('end', None)
                local_index_by_variable = copy.deepcopy(index_by_variable)
                local_index_by_variable[variable_name]['formula'] = individual_formula['formula']
                actual_years = list(set(range(
                    max(start, min(years)) if (start is not None) else min(years),
                    min(end + 1, max(years) + 1) if (end is not None) else (max(years) + 1),
                    )))
                variable_value, final_formula = get_or_construct_value(
                    df, variable_name, local_index_by_variable, actual_years, fill_value = fill_value)
                if variable_value.empty:
                    variable_value = pandas.DataFrame({variable_name: [fill_value]}, index = actual_years)
                    variable_value.index.name = 'year'
                result_data_frame = pandas.concat((result_data_frame, variable_value))

            return result_data_frame, 'formula changes accross time'

        parser_formula = Parser()
        expr = parser_formula.parse(formula)

        variables = expr.variables()
        for component in variables:
            variable_value, variable_formula = get_or_construct_value(
                df, component, index_by_variable, years, fill_value = fill_value)

            if index is None:
                index = variable_value.index
                assert len(variable_value.index) == len(variable_value.index.unique()), "Component {} does not have a single valued index {}".format(component, variable_value.index)
            else:
                try:
                    reindexing_condition = not(index == variable_value.index)
                except ValueError:
                    reindexing_condition = not(index == variable_value.index).all()
                if reindexing_condition:
                    log.info('index differs {} vs {} after getting {}'.format(
                        index, variable_value.index, component))
                    index = index.union(variable_value.index)
                    log.info('Will be using union index {}'.format(index))

            formula_with_parenthesis = '(' + variable_formula + ')'  # needs a nicer formula output
            final_formula = formula.replace(component, formula_with_parenthesis)
            dico_value[component] = variable_value

        formula_modified = formula.replace("^", "**")

        for component, variable_value in dico_value.iteritems():  # Reindexing
            if variable_value.empty:  # Dealing with completely absent variable
                variable_value = pandas.DataFrame({component: [fill_value]}, index = index)
            dico_value[component] = variable_value.reindex(index = years, fill_value = fill_value).values.squeeze()

        data = eval(formula_modified, dico_value)
        assert data is not None
        assert index is not None
        try:
            result_data_frame = pandas.DataFrame(
                data = {variable_name: data},
                index = index,
                )
        except Exception, e:
            print variable_name, data, index
            raise(e)

    return result_data_frame, final_formula


def get_or_construct_data(df, variable_dictionary, years = range(1949, 2014)):
    """
    Returns the DateFrame of the values of economic variables, fetched or calculated, for years of interest.
    Years are set to the index of the DataFrame.

    Parameters
    ----------
    df : DataFrame
        DataFrame generated by get_comptes_nationaux_data(year)
    variable_dictionary : dictionary
        Contains all economic variables denoted by their index. Variables for which formula is None will be directly
        fetched in the comptabilité nationale data (df). Those for which formula is not None will be calculated.
        Variables appearing in formulas should be in the index of variable_dictionary. If not interested in values of
        a variable, add 'drop':True in sub-dictionary variable_dictionary[variable].
    years : list of integers
        Years of interest

    Example
    --------
    >>> table_cn = get_comptes_nationaux_data(2013)
    >>> dict_RDM = {
    ...    'Interets_verses_par_rdm': {
    ...         'code': 'D41',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': '',
    ...         'drop': True,
    ...     },
    ...    'Dividendes_verses_par_rdm_D42': {
    ...         'code': 'D42',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Dividendes_verses_par_rdm_D43': {
    ...         'code': 'D43',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Revenus_propriete_verses_par_rdm': {
    ...         'code': 'D44',
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Interets_verses_au_rdm': {
    ...         'code': 'D41',
    ...         'institution': 'S2',
    ...         'ressources': True,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Dividendes_verses_au_rdm_D42': {
    ...         'code': 'D42',
    ...         'institution': 'S2',
    ...         'ressources': True,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Dividendes_verses_au_rdm_D43': {
    ...         'code': 'D43',
    ...         'institution': 'S2',
    ...         'ressources': True,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Revenus_propriete_verses_au_rdm': {
    ...         'code': 'D44',
    ...         'institution': 'S2',
    ...         'ressources': True,
    ...         'description': '',
    ...         'drop': True,
    ...    },
    ...    'Interets_dividendes_verses_par_rdm': {
    ...         'code': None,
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': 'Interets et dividendes verses par RDM',
    ...         'formula': 'Interets_verses_par_rdm + Dividendes_verses_par_rdm_D42 + Dividendes_verses_par_rdm_D43 + Revenus_propriete_verses_par_rdm' #analysis:ignore
    ...    },
    ...    'Interets_dividendes_nets_verses_par_rdm': {
    ...         'code': None,
    ...         'institution': 'S2',
    ...         'ressources': False,
    ...         'description': 'Interets et dividendes verses par RDM, nets',
    ...         'formula': 'Interets_verses_par_rdm + Dividendes_verses_par_rdm_D42 + Dividendes_verses_par_rdm_D43 + Revenus_propriete_verses_par_rdm - Interets_verses_au_rdm - Dividendes_verses_au_rdm_D42 - Dividendes_verses_au_rdm_D43 - Revenus_propriete_verses_au_rdm'  #analysis:ignore
    ...    }
    ... }
    >>> values_RDM, formulas_RDM = get_or_construct_data(df, dict_RDM)

    Returns a tuple, where the first element is a DataFrame for years 1949 to 2013 containing the sum of interests and
    dividends paid to France by the rest of the world, both gross and net of interests and dividends paid by France to
    the rest of the world ; and the second element is the dictionary of formulas, indexed by the calculated variables.
    """
    result = pandas.DataFrame()
    formulas = dict()

    for variable in variable_dictionary:
        variable_values, variable_formula = get_or_construct_value(df, variable, variable_dictionary, years)
        variable_name = variable.replace('_', ' ')

        if variable_dictionary[variable].get('formula') is not None:
            formulas[variable_name] = variable_formula

        drop = variable_dictionary[variable].get('drop')
        if not drop:
            result = pandas.concat((result, variable_values), axis=1)
        else:
            continue

    return result, formulas
