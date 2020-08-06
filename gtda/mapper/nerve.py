"""Construct the nerve of a refined Mapper cover."""
# License: GNU AGPLv3

from functools import reduce
from itertools import combinations
from operator import iconcat

import igraph as ig
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


def _fixed_points(mapping):
    terminal_states = []
    for i in range(len(mapping)):
        j = i
        k = mapping[i]
        while j != k:
            j = mapping[j]
            k = mapping[mapping[j]]
        terminal_states.append(j)
    return terminal_states


class Nerve(BaseEstimator, TransformerMixin):
    """1-skeleton of the nerve of a refined Mapper cover, i.e. the Mapper
    graph.

    This transformer is the final step in the
    :class:`gtda.mapper.pipeline.MapperPipeline` objects created
    by :func:`gtda.mapper.make_mapper_pipeline`. It corresponds the last two
    arrows in `this diagram <../../../../_images/mapper_pipeline.svg>`_.

    This transformer is not intended for direct use.

    Parameters
    ----------
    min_intersection : int, optional, default: ``1``
        Minimum size of the intersection, between data subsets associated to
        any two Mapper nodes, required to create an edge between the nodes in
        the Mapper graph.

    store_edge_elements : bool, optional, default: ``False``
        Whether the indices of data elements associated to Mapper edges (i.e.
        in the intersections allowed by `min_intersection`) should be stored in
        the :class:`igraph.Graph` object output by :meth:`fit_transform`. When
        ``True``, might lead to a large :class:`igraph.Graph` object.

    contract_nodes : bool, optional, default: ``False``
        TODO write

    Attributes
    ----------
    graph_ : :class:`igraph.Graph` object
        Mapper graph obtained from the input data. Created when :meth:`fit` is
        called.

    """

    def __init__(self, min_intersection=1, store_edge_elements=False,
                 contract_nodes=False):
        self.min_intersection = min_intersection
        self.store_edge_elements = store_edge_elements
        self.contract_nodes = contract_nodes

    def fit(self, X, y=None):
        """Compute the Mapper graph as in :meth:`fit_transform`, but store the
        graph as :attr:`graph_` and return the estimator.

        Parameters
        ----------
        X : list of list of tuple
            See :meth:`fit_transform`.

        y : None
            There is no need for a target in a transformer, yet the pipeline
            API requires this parameter.

        Returns
        -------
        self : object

        """
        self.graph_ = self.fit_transform(X, y=y)
        return self

    def fit_transform(self, X, y=None):
        """Construct a Mapper graph from a refined Mapper cover.

        Parameters
        ----------
        X : list of list of tuple
            Data structure describing a cover of a dataset (e.g. as depicted in
            `this diagram <../../../../_images/mapper_pipeline.svg>`_) produced
            by the clustering step of a :class:`gtda.mapper.MapperPipeline`.
            Each sublist corresponds to a (non-empty) pullback cover set --
            equivalently, to a cover set in the filter range which has
            non-empty preimage. It contains triples of the form ``(\
            pullback_set_label, partial_cluster_label, node_elements)`` where
            ``partial_cluster_label`` is a cluster label within the pullback
            cover set identified by ``pullback_set_label``, and
            ``node_elements`` is an array of integer indices. To each pair
            ``(pullback_set_label, partial_cluster_label)`` there corresponds
            a unique node in the output Mapper graph. This node represents
            the data subset defined by the indices in ``node_elements``.

        y : None
            There is no need for a target in a transformer, yet the pipeline
            API requires this parameter.

        Returns
        -------
        graph : :class:`igraph.Graph` object
            Undirected Mapper graph according to `X` and `min_intersection`.
            Each node is an :class:`igraph.Vertex` object with attributes
            ``"pullback_set_label"``, ``"partial_cluster_label"`` and
            ``"node_elements"'``. Each edge is an :class:`igraph.Edge` object
            with a ``"weight"`` attribute which is equal to the size of the
            intersection between the data subsets associated to its two nodes.
            If `store_edge_elements` is ``True`` each edge also has an
            additional attribute ``"edge_elements"``.

        """
        # TODO: Include a validation step for X
        # Graph construction -- vertices with their metadata
        nodes = reduce(iconcat, X, [])
        graph = ig.Graph(len(nodes))

        # Since `nodes` is a list, say of length N, of triples of the form
        # (pullback_set_label, partial_cluster_label, node_elements),
        # zip(*nodes) generates three tuples of length N, each corresponding to
        # a type of node attribute.
        node_attributes = zip(*nodes)
        graph.vs["pullback_set_label"] = next(node_attributes)
        graph.vs["partial_cluster_label"] = next(node_attributes)
        node_elements = next(node_attributes)
        graph.vs["node_elements"] = node_elements

        # Graph construction -- edges with weights given by intersection sizes
        node_index_pairs, weights, intersections, mapping = \
            self._generate_edge_data(node_elements)
        graph.es["weight"] = 1
        graph.add_edges(node_index_pairs)
        graph.es["weight"] = weights
        if self.store_edge_elements:
            graph.es["edge_elements"] = intersections
        if self.contract_nodes:
            fixed_points_mapping = _fixed_points(mapping)
            graph.contract_vertices(
                fixed_points_mapping, combine_attrs="first"
                )
            graph.delete_vertices(
                [i for i in graph.vs.indices if i != fixed_points_mapping[i]]
                )

        return graph

    def _generate_edge_data(self, node_elements):
        node_tuples = combinations(enumerate(node_elements), 2)

        node_index_pairs = []
        weights = []
        intersections = []

        if self.contract_nodes:
            mapping = list(range(len(node_elements)))
        else:
            mapping = None

        # Boilerplate is just to avoid boolean checking at each iteration
        if not self.store_edge_elements:
            for (node_1_idx, node_1_elements), (node_2_idx, node_2_elements) \
                    in node_tuples:
                intersection = np.intersect1d(node_1_elements, node_2_elements)
                intersection_size = len(intersection)

                if self.contract_nodes:
                    if intersection_size == len(node_2_elements):
                        mapping[node_2_idx] = node_1_idx
                        continue
                    elif intersection_size == len(node_1_elements):
                        mapping[node_1_idx] = node_2_idx
                        continue
                    elif intersection_size >= self.min_intersection:
                        node_index_pairs.append((node_1_idx, node_2_idx))
                        weights.append(intersection_size)
                elif intersection_size >= self.min_intersection:
                    node_index_pairs.append((node_1_idx, node_2_idx))
                    weights.append(intersection_size)
        else:
            for (node_1_idx, node_1_elements), (node_2_idx, node_2_elements) \
                    in node_tuples:
                intersection = np.intersect1d(node_1_elements, node_2_elements)
                intersection_size = len(intersection)

                if self.contract_nodes:
                    if intersection_size == len(node_2_elements):
                        mapping[node_2_idx] = node_1_idx
                        continue
                    elif intersection_size == len(node_1_elements):
                        mapping[node_1_idx] = node_2_idx
                        continue
                    elif intersection_size >= self.min_intersection:
                        node_index_pairs.append((node_1_idx, node_2_idx))
                        weights.append(intersection_size)
                        intersections.append(intersection)
                elif intersection_size >= self.min_intersection:
                    node_index_pairs.append((node_1_idx, node_2_idx))
                    weights.append(intersection_size)
                    intersections.append(intersection)

        return node_index_pairs, weights, intersections, mapping
