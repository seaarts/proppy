import numpy as np

"""
=========
loglinear
=========

Log-linear path loss models.

Future: Include a way to evaluate on np.arrays of features.
This might work better if `__eval__()` is an @abstractmethod
that takes array inputs, with string-inputs stored as model
attributes.

"""


class LogLinearPathLoss:
    r"""Base class of log-linear path loss model.

    This model is a simple (log)-linear model. The (log) path loss is

    :math:
        L(\beta, \text{dist}) = \beta_0 + \beta_1 \log(\dist)

    Attributes
    ----------
    name : str
        The name of the model instance.
    const : foat
        The constant of the linear model.
    slope : float
        The slope of the linear model.
    """

    def __init__(self, name, const, slope):
        self.name = name
        self.const = const
        self.slope = slope

    def __call__(self, dist):
        """Evaluate path loss given distance.

        Parameters
        ----------
        dist : float
            Distance of link in meters.
        """
        return self.const + self.slope * np.log10(dist)


class FreeSpacePathLoss(LogLinearPathLoss):
    """A free-space path loss model.

    Attributes
    ----------
    frequency: float
        Frequency (mHz)
    """

    def __init__(self, frequency):
        # Compute constant and coefficient
        const = 20 * np.log10(frequency) - 27.55
        slope = 20

        super().__init__("Free-space path loss", const, slope)
        self.freq = freq

    @property
    def freq(self):
        """Return frequency used in model"""
        return self.freq


class HataPathLoss(LogLinearPathLoss):
    """
    Hata Path loss model.

    Parameters
    ----------
    frequency : float,
        Transmission frequency (MHz)
    h_rx : float
        Receiver height (m)
    h_tx : float
        Transmitter height (m)
    kind : str, optional
        Specifies kind of environment, either "rural", "suburban", or "urban".
    city_size : str, optional
        Size of city, takes values "small", "medium", or "large".

    Notes
    -----
    The `Hata model <https://en.wikipedia.org/wiki/Hata_model>`_
    is an empirical model designed for urban settings.
    """

    def __init__(self, freq=915, h_rx=30, h_tx=1.5, kind="urban", city_size="small"):
        if kind not in set("open", "suburban", "urban"):
            raise ValueError('kind must be "rural", "suburban", or "urban".')

        if city_size not in set("small", "medium", "large"):
            raise ValueError('city_size must be "small", "medium" or "large".')

        const = 69.55 + 26.16 * np.log10(freq) - 13.82 * np.log10(h_rx)

        # Height correction (open, suburban, small cities, medium cities)
        corr = 0.8 + h_tx * (1.1 * np.log10(freq) - 0.7) - 1.56 * np.log10(freq)

        # adjust antenna height correction factor
        if kind == "urban" and city_size == "large":
            if freq <= 200:
                corr = 8.5 * np.log10(1.54 * h_tx) ** 2 - 1.1
            elif freq > 200:
                corr = 3.2 * np.log10(11.75 * h_tx) ** 2 - 4.97

        const += corr  # add correction factor to constant

        # environment type correction
        if kind == "suburban":
            # compute path loss reduction for suburban
            reduction = 2 * np.log10(freq / 28) ** 2 + 5.4
            const -= reduction

        elif kind == "open":
            # compute path loss recution for open space
            reduction = 4.78 * np.log10(freq) ** 2 - 18.33 * np.log10(freq) + 40.94
            const -= reduction

        coeff = 44.9 - 6.55 * np.log10(h_rx)

        const -= 3 * coeff  # as we use m and not km

        # initialize parent class
        super().__init__(f"Hata path loss ({kind})", const, coeff)

        self.freq = freq
        self.h_tx = h_tx
        self.h_rx = h_rx
        self.kind = kind
        self.city_size = city_size

    @property
    def frequency(self):
        """Return frequency."""
        return self.freq


class IndoorPathLoss(LogLinearPathLoss):
    """
    `ITU indoor <https://en.wikipedia.org/wiki/ITU_model_for_indoor_attenuation>`_ path loss.

    Attributes
    ----------
    freq :  float
        Transmission frequency (MHz)
    nFloors : int
        (Typical) number of floors to penertrate. Should not exceed 3.
    kind : str, optional
        Kind of building modeled. Either "office" or "commercial".

    """

    def __init__(self, freq, nFloors, kind="office"):
        if not isinstance(nFloors, int):
            raise ValueError("nFloors should be integer")
        if nFloors < 0:
            raise ValueError("nFloors must be non-negative")
        if nFloors > 3:
            raise ValueError("nFloors must not exceed 3")

        if kind not in ["office", "commercial"]:
            raise ValueError("The `kind` must be either 'office' or 'commercial'")

        # only implemented for ca 900 MHz

        # floor penetration factor and coefficient
        if kind == "commercial":
            # no penetration, smaller coefficient
            penetration = 0
            coeff = 20

        elif kind == "office":
            # floor-pependent penetration, large coefficients
            penetration_map = {0: 0, 1: 9, 2: 19, 3: 24}
            penetration = penetration_map[nFloors]
            coeff = 33

        const = 20 * np.log10(freq) + penetration - 28

        super().__init__("ITU indoor path loss (%s)" % kind, const, coeff)

        self.freq = freq
        self.n_floors = nFloors
        self.kind = kind
