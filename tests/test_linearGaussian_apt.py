import pytest
import torch
from torch import distributions

import sbi.utils as utils
from sbi.inference.snpe.snpe_c import APT
from sbi.simulators.linear_gaussian import (
    get_ground_truth_posterior_samples_linear_gaussian,
    linear_gaussian
)

# use cpu by default
torch.set_default_tensor_type("torch.FloatTensor")

# seed the simulations
torch.manual_seed(0)


@pytest.mark.parametrize("num_dim", [1, 3])
def test_apt_on_linearGaussian_based_on_mmd(num_dim):

    prior = distributions.MultivariateNormal(
        loc=torch.zeros(num_dim), covariance_matrix=torch.eye(num_dim)
    )

    true_observation = torch.zeros((1, num_dim))

    apt = APT(
        simulator=linear_gaussian,
        true_observation=true_observation,
        prior=prior,
        num_atoms=-1,
        z_score_obs=True,
        use_combined_loss=False,
        retrain_from_scratch_each_round=False,
        discard_prior_samples=False,
    )

    # run inference
    num_rounds, num_simulations_per_round = 1, 1000
    apt.run_inference(
        num_rounds=num_rounds, num_simulations_per_round=num_simulations_per_round
    )

    # draw samples from posterior
    samples = apt._neural_posterior.sample(1000)

    # define target distribution (analytically tractable) and sample from it
    target_samples = get_ground_truth_posterior_samples_linear_gaussian(
        true_observation
    )

    # compute the mmd
    mmd = utils.unbiased_mmd_squared(target_samples, samples)

    # check if mmd is larger than expected
    max_mmd = 0.02

    assert (
        mmd < max_mmd
    ), f"MMD={mmd} is more than 2 stds above the average performance."
