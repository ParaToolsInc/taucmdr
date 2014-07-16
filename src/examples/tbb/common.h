/*
    Copyright 2005-2013 Intel Corporation.  All Rights Reserved.

    The source code contained or described herein and all documents related
    to the source code ("Material") are owned by Intel Corporation or its
    suppliers or licensors.  Title to the Material remains with Intel
    Corporation or its suppliers and licensors.  The Material is protected
    by worldwide copyright laws and treaty provisions.  No part of the
    Material may be used, copied, reproduced, modified, published, uploaded,
    posted, transmitted, distributed, or disclosed in any way without
    Intel's prior express written permission.

    No license under any patent, copyright, trade secret or other
    intellectual property right is granted to or conferred upon you by
    disclosure or delivery of the Materials, either expressly, by
    implication, inducement, estoppel or otherwise.  Any license under such
    intellectual property rights must be express and approved by Intel in
    writing.
*/

typedef float Value;

struct TreeNode {
    //! Pointer to left subtree
    TreeNode* left; 
    //! Pointer to right subtree
    TreeNode* right;
    //! Number of nodes in this subtree, including this node.
    long node_count;
    //! Value associated with the node.
    Value value;
};

Value SerialSumTree( TreeNode* root );
Value SimpleParallelSumTree( TreeNode* root );
Value OptimizedParallelSumTree( TreeNode* root );
