from app.losses import coupling_loss, total_loss


def test_coupling_loss_positive_weight() -> None:
    assert coupling_loss(0.9) < coupling_loss(0.1)


def test_total_loss_adds_terms() -> None:
    loss = total_loss(ce=0.5, couple_w=0.8, conf=0.4)
    assert loss > 0.5
