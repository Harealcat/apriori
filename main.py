import itertools
import argparse


def main():
    # flags and arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--support", type=int,
                        help='support to get tuples')
    parser.add_argument("-n", "--n_items", type=int, help='number of items')
    parser.add_argument("-t", "--threshold", type=float, default=0.8, help='threshold for confidence')
    parser.add_argument("filename", help='filename with data')
    args = parser.parse_args()

    # get args
    filename = args.filename
    support = args.support
    n_items = args.n_items
    threshold = args.threshold

    # get set of frequent tuples and a map with a counter for each tuple
    frequent_sets, support_map = apriori(filename, support, n_items)

    # get the rules found for given confidence
    rules = find_rules(frequent_sets, support_map, threshold)

    # print rules to terminal
    print('ALL RULES :')
    print()
    for i in range(len(rules)):
        x = rules[i][0]
        y = tuple(rules[i][1])
        if len(y) == 1:
            y = y[0]
        print(f'rule{i} : {x} => {y}')


def apriori(filename, support, n_items):
    # list that will contain all frequent tuples
    frequent_sets = []

    # dict that will contain the support count for each tuple in frequent_set
    support_map = {}

    # compute frequent singletons
    f_singletons = frequent_singletons(filename, support, n_items, support_map)

    print("#########################################################################################################")
    print("frequent singletons :")
    print("")
    print(f_singletons)
    print("#########################################################################################################")

    # compute frequent pairs
    f_pairs = frequent_pairs(f_singletons, support, filename, support_map)

    print("frequent pairs :")
    print("")
    print(f_pairs)
    print("#########################################################################################################")

    # append singletons to frequent set
    frequent_sets.append(f_singletons)
    # append pairs to frequent set
    frequent_sets.append(f_pairs)

    # construct k+1 and filter k+1 until it return an empty set, start with k = 3
    k = 3
    while k != 0:

        # construct k+1
        ck = construct_k_plus_one(frequent_sets)

        # if already empty no need to filter
        if len(ck) < 1:
            break

        # filter k+1
        k_tuples = filter_k_plus_one(ck, k, support, filename, support_map)

        # if not empty, print set and add it to frequent _set
        if len(k_tuples) >= 1:
            print(f'frequent {k}_tuples:')
            print("")
            print(k_tuples)
            print(
                "###########################################################"
                "##############################################")

            frequent_sets.append(k_tuples)
            k += 1
        # if empty, stop the loop
        else:
            k = 0

    return frequent_sets, support_map


def frequent_singletons(filename, support, n_items, support_map):
    # set for our frequent singletons
    singletons = set()
    # list to count singletons in baskets
    counter_singletons = [0] * n_items

    # open file and read it
    with open(filename) as baskets:
        # for every line
        for basket in baskets:
            # get items (separated by white spaces)
            items = basket.split()
            # for all item in previous list
            for item in items:
                # add 1 to counter of item
                counter_singletons[int(item)] += 1

    # get the singletons with support more than given support and them to set
    for i in range(n_items):
        # get the number of occurrences for item i
        counter = counter_singletons[i]
        # if more than support
        if counter > support:
            # add to set
            singletons.add(i)
            # update support map
            support_map[i] = counter
    return singletons


def frequent_pairs(f_singletons, support, filename, support_map):
    # number of frequent singletons
    m = len(f_singletons)
    # set that will contain pairs
    f_pairs = set()

    # initialize triangular matrix
    n_triangular_matrix = int(((m * (m - 1)) / 2) + 1)
    triangular_matrix = [0] * n_triangular_matrix

    # we remap the singletons from 1,..., m
    hash_map = {}
    x = 1
    for singleton in f_singletons:
        hash_map[singleton] = x
        x += 1

    # pass the dataset
    with open(filename) as baskets:
        # for each line
        for basket in baskets:
            # list of items for current basket
            items = basket.split()
            n = len(items)

            # 2 nested loops to create all possible pairs with items
            for i in range(n - 1):
                item1 = int(items[i])
                # we verify that item1 is in the list of frequent singletons, otherwise no need to continue
                if item1 in f_singletons:
                    for j in range(i + 1, n):
                        item2 = int(items[j])
                        # same condition for item2
                        if item2 in f_singletons:
                            # we get index of items stored in hash map
                            index1 = hash_map[item1]
                            index2 = hash_map[item2]

                            # update counter in triangular matrix
                            if index1 > index2:
                                index = int((index2 - 1) * (m - index2 / 2) + index1 - index2)
                            else:
                                index = int((index1 - 1) * (m - index1 / 2) + index2 - index1)
                            triangular_matrix[index] += 1

    # singletons as list
    singletons = list(hash_map)

    # get the pair values and add them to set, as for the support map
    i, j = 1, 1
    for count in triangular_matrix:
        if count > support:
            item1 = singletons[i - 1]
            item2 = singletons[j - 1]
            f_pairs.add((item1, item2))
            support_map[(item1, item2)] = count
        j += 1
        if j > m:
            i += 1
            j = i + 1

    return f_pairs


def construct_k_plus_one(frequent_sets):
    # get Lk
    list_k_tuples = frequent_sets[-1]
    # get singletons to construct ck+1
    f_singletons = frequent_sets[0]

    n = len(frequent_sets)
    ck = set()

    # for tuples in Lk
    for k_tuple in list_k_tuples:
        # for all singletons
        for singleton in f_singletons:
            # cast tuple to set
            new_set = set(k_tuple)
            m = len(new_set)

            # we add singleton to set, if already in it, won't add
            new_set.add(singleton)

            # if size changed (it means that we have created a potential new tuple)
            if m != len(new_set):

                # we test if all subsets of this new tuple ére in frequent sets, if not disregard it
                is_valid = True
                for i in range(1, n):
                    # set of all subsets of new_set of size i+1, actually return a set of tuples
                    all_possible_subsets = findsubsets(new_set, i + 1)
                    # some sorting (items must be in ascendant order)
                    all_possible_subsets = set([tuple(sorted(x)) for x in all_possible_subsets])

                    # check if it's a subset or not of frequent sets
                    if not all_possible_subsets.issubset((frequent_sets[i])):
                        is_valid = False
                        break

                # if all subsets are in frequent set, we can add it to ck
                if is_valid:
                    new_tuple = tuple(sorted(new_set))
                    ck.add(new_tuple)
    return ck


def filter_k_plus_one(ck, k, support, filename, support_map):
    # set Lk+1
    f_k = set()

    # we use a hash map to store counters, all 0s at beginning
    hash_map = {}
    for k_tuple in ck:
        hash_map[k_tuple] = 0

    with open(filename) as baskets:
        # for each line
        for basket in baskets:
            # list of items
            items = basket.split()
            # cast list of items to set of items
            items = set([int(x) for x in items])
            # set of all possible subsets of items of size k
            k_possible_tuples = findsubsets(items, k)
            # some sorting
            k_possible_tuples = set([tuple(sorted(x)) for x in k_possible_tuples])

            # update counter if subset in ck
            for k_possible_tuple in k_possible_tuples:
                if k_possible_tuple in ck:
                    hash_map[k_possible_tuple] += 1

    # add k_tuple to Lk+1 if counter more than support
    for k_tuple in ck:
        if hash_map[k_tuple] > support:
            f_k.add(k_tuple)
        else:
            # we want to update our support map so we can just delete useless counters in hash map and then update
            del hash_map[k_tuple]
    support_map.update(hash_map)
    return f_k


def findsubsets(S, m):
    # nice module to get all subsets of size m from a set S
    return set(itertools.combinations(S, m))


def find_rules(frequent_sets, support_map, threshold):
    # list of rules
    rules = []
    n = len(frequent_sets)

    # 3 nested loops to create all possible rules
    # for each (i+1)_tuples i>=1
    for i in range(1, n):
        x = frequent_sets[i]
        # for each tuple in i+1_tuples

        for k_tuple in x:
            # all subsets will contain all subsets of size 1 to i of i+1_tuple
            all_subsets = set()
            # cast tuple to set (for itertools)
            set_k_tuple = set([int(y) for y in k_tuple])

            # update all subsets created of size 1 to i
            for j in range(1, i + 1):
                all_subsets.update(findsubsets(set_k_tuple, j))
            # some sorting
            all_subsets = set([tuple(sorted(x)) for x in all_subsets])

            # for each subsets, we compute confidence, if more than threshold, we can add it to rules
            for subset in all_subsets:

                # this part not important, just some formatting (itertools return tuples for singletons :c)
                is_single = False
                if len(subset) == 1:
                    is_single = True
                    subset = subset[0]

                # compute confidence
                confidence = support_map[k_tuple] / support_map[subset]

                # if confidence more than threshold
                if confidence >= threshold:
                    # create a copy of i+1_tuple to work with
                    res = set_k_tuple.copy()

                    # we compute k_tuple \ subset, and again some formatting for singletons
                    if not is_single:
                        for item in subset:
                            res.remove(item)
                    else:
                        res.remove(subset)
                    # we can append the rule
                    rules.append([subset, res])
    return rules


main()
