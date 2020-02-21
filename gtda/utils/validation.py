"""Utilities for input validation."""
# License: GNU AGPLv3

import numbers
import types
import numpy as np

from sklearn.utils.validation import check_array

available_metrics = {
    'bottleneck': [('delta', numbers.Number, (0., 1.))],
    'wasserstein': [('p', int, (1, np.inf)),
                    ('delta', numbers.Number, (1e-16, 1.))],
    'betti': [('p', numbers.Number, (1, np.inf)),
              ('n_bins', int, (1, np.inf))],
    'landscape': [('p', numbers.Number, (1, np.inf)),
                  ('n_bins', int, (1, np.inf)),
                  ('n_layers', int, (1, np.inf))],
    'heat': [('p', numbers.Number, (1, np.inf)),
             ('n_bins', int, (1, np.inf)),
             ('sigma', numbers.Number, (0., np.inf))],
    'persistence_image': [('p', numbers.Number, (1, np.inf)),
                          ('n_bins', int, (1, np.inf)),
                          ('sigma', numbers.Number, (0., np.inf)),
                          ('weight_function', types.FunctionType,
                           None)]}

available_metric_params = {metric: [p[0] for p in param_lst]
                           for metric, param_lst in available_metrics.items()}


def check_diagram(X, copy=False):
    """Input validation on a diagram
    """
    if len(X.shape) != 3:
        raise ValueError("X should be a 3d np.array: X.shape"
                         " = {}".format(X.shape))
    if X.shape[2] != 3:
        raise ValueError("X should be a 3d np.array with a 3rd dimension of"
                         " 3 components: X.shape[2] = {}".format(X.shape[2]))

    homology_dimensions = sorted(list(set(X[0, :, 2])))
    for dim in homology_dimensions:
        if dim == np.inf:
            if len(homology_dimensions) != 1:
                raise ValueError("np.inf is a valid homology dimension for a "
                                 "stacked diagram but it should be the only "
                                 "one: homology_dimensions "
                                 "= {}".format(homology_dimensions))
        else:
            if dim != int(dim):
                raise ValueError("All homology dimensions should be"
                                 " integer valued: {} can't be casted"
                                 " to an int of the same value.".format(dim))
            if dim != np.abs(dim):
                raise ValueError("All homology dimensions should be"
                                 " integer valued: {} can't be casted"
                                 " to an int of the same value.".format(dim))

    n_points_above_diag = np.sum(X[:, :, 1] >= X[:, :, 0])
    n_points_global = X.shape[0] * X.shape[1]
    if n_points_above_diag != n_points_global:
        raise ValueError("All points of all n_samples persistent diagrams "
                         "should be above the diagonal, X[:,:,1] >= X[:,:,0]."
                         " {} points in "
                         "all n_samples diagrams are under the diagonal."
                         "".format(n_points_global - n_points_above_diag))
    if copy:
        return np.copy(X)
    else:
        return X


def check_graph(X):
    return X


# Check the type and range of numerical parameters
def validate_params(parameters, references):
    for key in references.keys():
        if not isinstance(parameters[key], references[key][0]):
            raise TypeError("Parameter {} is of type {}"
                            " while it should be of type {}"
                            "".format(key, type(parameters[key]),
                                      references[key][0]))
        if len(references[key]) == 1:
            continue
        if references[key][0] == list or \
                references[key][0] == np.ndarray:
            for parameter in parameters[key]:
                if references[key][1][0] == int:
                    if not isinstance(parameter, numbers.Number):
                        raise TypeError("Parameter {} is a {} of {}"
                                        " but contains an element of type {}"
                                        "".format(key, type(parameters[key]),
                                                  references[key][1][0],
                                                  type(parameter)))
                    if not float(parameter).is_integer():
                        raise TypeError("Parameter {} is a {} of int"
                                        " but contains an element of type {}"
                                        " that is not an integer."
                                        "".format(key, type(parameters[key]),
                                                  type(parameter)))
                else:
                    if not isinstance(parameter, references[key][1][0]):
                        raise TypeError("Parameter {} is a {} of {}"
                                        " but contains an element of type {}"
                                        "".format(key, type(parameters[key]),
                                                  references[key][1][0],
                                                  type(parameter)))
                if references[key][1][1] is None:
                    break
                if isinstance(references[key][1][1], tuple):
                    if (parameter < references[key][1][1][0] or
                            parameter > references[key][1][1][1]):
                        raise ValueError("Parameter {} is a list containing {}"
                                         "which should be in the range [{},{}]"
                                         "".format(key, parameter,
                                                   references[key][1][1][0],
                                                   references[key][1][1][1]))
            break
        if references[key][1][1] is None:
            break
            for parameter in parameters[key]:
                if isinstance(references[key][1], tuple):
                    if (parameter < references[key][1][1][0] or
                            parameter > references[key][1][1][1]):
                        raise ValueError(
                            "Parameter {} is an array containing {} which "
                            "should be in the range [{},{}]".format(
                                key, parameter, references[key][1][1][0],
                                references[key][1][1][1]))
            break
        if isinstance(references[key][1], tuple):
            if (parameters[key] < references[key][1][0] or
                    parameters[key] > references[key][1][1]):
                raise ValueError("Parameter {} is {}, while it"
                                 " should be in the range [{}, {}]"
                                 "".format(key, parameters[key],
                                           references[key][1][0],
                                           references[key][1][1]))
        if isinstance(references[key][1], list):
            if parameters[key] not in references[key][1]:
                raise ValueError("Parameter {} is {}, while it"
                                 " should be one of the following {}"
                                 "".format(key, parameters[key],
                                           references[key][1]))


def validate_metric_params(metric, metric_params):
    if metric not in available_metrics.keys():
        raise ValueError("No metric called {}."
                         " Available metrics are {}."
                         "".format(metric,
                                   list(available_metrics.keys())))

    for (param, param_type, param_values) in available_metrics[metric]:
        if param in metric_params.keys():
            input_param = metric_params[param]
            if not isinstance(input_param, param_type):
                raise TypeError("{} in params_metric is of type {}"
                                " but must be an {}."
                                "".format(param, type(input_param),
                                          param_type))
            if param_values is not None:
                if input_param < param_values[0] or \
                        input_param > param_values[1]:
                    raise ValueError("{} in param_metric should be between {} "
                                     "and {} but has been set to {}."
                                     "".format(param, param_values[0],
                                               param_values[1], input_param))

    for param in metric_params.keys():
        if param not in available_metric_params[metric]:
            raise ValueError("{} in metric_param is not an available"
                             " parameter. Available metric_params"
                             " are {}".format(param,
                                              available_metric_params[metric]))


def check_list_of_images(X, **kwargs):
    """Check a list of arrays representing images, by integrating
    through the input one by one. To pass a test when `kwargs` is ``None``,
    all images ``x`` in `X` must satisfy:
        - ``x.ndim`` >= 2,
        - ``all(np.isfinite(x))``

    Parameters
    ----------
    X : list of ndarray
        Each entry of `X` corresponds to an image.

    kwargs : dict or None, optional, default: ``None``
        Parameters accepted by
        :func:`~gtda.utils.validation.check_list_of_arrays`.

    Returns
    -------
    X : list of ndarray
        as modified by :func:`~sklearn.utils.validation.check_array`

    """
    kwargs_default = {'force_same_n_axis': False,
                      'force_same_shape': False, 'force_all_finite': True,
                      'ensure_2d': False, 'allow_nd': True}
    kwargs_default.update(kwargs)
    return check_list_of_arrays(X, **kwargs_default)


def check_list_of_point_clouds(X, **kwargs):
    """Check a list of arrays representing point clouds, by integrating
    through the input one by one. To pass a test when `kwargs` is ``None``,
    all point clouds ``x``, ``y`` in X must satisfy:
        - ``x.ndim == 2``,
        - ``len(y.shape) == len(y.shape)``.

    Parameters
    ----------
    X : list of ndarray, such that `X[i].ndim==2` (n_points, n_dimensions),
        or an array `X.dim==3`

    kwargs : dict or None, optional, default: ``None``
        Parameters accepted by
        :func:`~gtda.utils.validation.check_list_of_arrays`.

    Returns
    -------
    X : list of input arrays
        as modified by :func:`~sklearn.utils.validation.check_array`

    """
    kwargs_default = {'ensure_2d': True, 'force_all_finite': False,
                      'force_same_shape': False, 'force_same_n_axis': True}
    kwargs_default.update(kwargs)
    return check_list_of_arrays(X, **kwargs_default)


def check_list_of_arrays(X, force_same_shape=True, force_same_n_axis=True,
                         **kwargs):
    """Check a list of arrays, by integrating through the input one by one.
    The constraints are to be specified in :param:`kwargs`. On top of
    parameters from :func:`~sklearn.utils.validation.check_array`,
    the optional parameters are listed below.

    Parameters
    ----------
    X : list(ndarray), such that `X[i].ndim==2` (n_points, n_dimensions),
        or an array `X.dim==3`

    force_same_shape : bool, optional, default: ``True``
        Indicates whether the shapes of the elements of X should all
        be the same.

    force_same_n_axis : bool, optional, default: ``True``
        Indicates whether the number of axes in the elements of X should all
        be the same.

    kwargs: dict or None, optional, default: ``None``
        Parameters accepted by :func:`~sklearn.utils.validation.check_array`.

    Returns
    -------
    X : list of input arrays
        as modified by :func:`~sklearn.utils.validation.check_array`

    """

    # if restrictions on the dimensions of the input are imposed
    if force_same_shape:
        shapes = [x.shape for x in X]
        if not (all([shapes[0] == s for s in shapes])):
            raise ValueError(f"The arrays in X do not have the same dimensions"
                             "({shapes}), while they should.")
    # if the number of dimensions can vary
    elif force_same_n_axis:
        n_axis = [x.ndim for x in X]
        if not (all([n_axis[0] == n for n in n_axis])):
            raise ValueError(f"The arrays in X do not have the same number"
                             "of axes ({n_axis}), while they should.")

    is_check_failed = False
    messages = []
    for i, x in enumerate(X):
        try:
            # TODO: verifythe behavior depending on copy.
            X[i] = check_array(x, **kwargs)
            messages = ['']
        except ValueError as e:
            is_check_failed = True
            messages.append(str(e))
    if is_check_failed:
        raise ValueError("The following errors were raised" +
                         "by the inputs: \n" + "\n".join(messages))
    else:
        return X
