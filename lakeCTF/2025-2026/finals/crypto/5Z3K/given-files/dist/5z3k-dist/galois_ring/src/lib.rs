/// Please don't waste time on this, it's just a translation of galois_ring.py to make everything go fast
/// Nyooooooom
///
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyType;

trait ToJson {
    type JSON;
}

macro_rules! z2k {
    ($k: literal, $ty: ident) => {
        #[pyclass(module = "_galois_ring")]
        #[derive(Clone, Default)]
        struct $ty {
            pub(crate) v: u64,
        }

        impl ToJson for $ty {
            type JSON = u64;
        }

        #[pymethods]
        impl $ty {
            const MASK: u64 = (1u64 << $k) - 1;

            #[new]
            fn new(v: &Bound<'_, PyAny>) -> PyResult<Self> {
                Ok(if v.is_none() {
                    Self { v: 0 }
                } else if let Ok(x) = v.extract::<Self>() {
                    x
                } else {
                    Self {
                        v: v.extract::<u64>()?,
                    }
                })
            }

            fn __int__(&self) -> u64 {
                self.v
            }

            #[staticmethod]
            fn total_degree() -> u64 {
                1
            }

            #[staticmethod]
            fn two_adicity() -> u64 {
                $k
            }

            #[staticmethod]
            fn sample(rng: Bound<'_, PyAny>) -> PyResult<Self> {
                let result = rng.getattr("get")?.call0()?;
                let bytes: &[u8] = result.extract()?;
                let mut buf = [0u8; 8];
                if bytes.len() < 8 {
                    return Err(PyErr::new::<PyTypeError, _>("rng returned too few bytes"));
                }
                buf[..].copy_from_slice(&bytes[bytes.len() - 8..]);
                Ok(Self {
                    v: u64::from_be_bytes(buf) & Self::MASK,
                })
            }

            #[staticmethod]
            fn zero() -> Self {
                Self { v: 0 }
            }

            #[staticmethod]
            fn one() -> Self {
                Self { v: 1 }
            }

            #[staticmethod]
            fn exseq_size() -> usize {
                2
            }

            #[staticmethod]
            fn exseq(i: usize) -> Self {
                Self { v: i as u64 & 1 }
            }

            fn is_zero(&self) -> bool {
                self.v == 0
            }

            fn __add__(&self, other: &Self) -> Self {
                Self {
                    v: self.v.wrapping_add(other.v) & Self::MASK,
                }
            }

            fn __sub__(&self, other: &Self) -> Self {
                Self {
                    v: self.v.wrapping_sub(other.v) & Self::MASK,
                }
            }

            fn __mul__(&self, other: &Self) -> Self {
                Self {
                    v: self.v.wrapping_mul(other.v) & Self::MASK,
                }
            }

            fn __neg__(&self) -> Self {
                Self::zero().__sub__(self)
            }

            fn inv(&self) -> PyResult<Self> {
                if self.v & 1 == 0 {
                    Err(PyErr::new::<PyValueError, _>("Not invertible"))
                } else {
                    Ok(self.__pow__(Self::MASK, None))
                }
            }

            fn __pow__(&self, mut exp: u64, _m: Option<u64>) -> Self {
                let mut res = Self::one();
                let mut b = Self { v: self.v };
                while exp > 0 {
                    if exp & 1 == 1 {
                        res = res.__mul__(&b);
                    }
                    b = b.__mul__(&b);
                    exp >>= 1;
                }
                res
            }

            fn __truediv__(&self, other: &Self) -> PyResult<Self> {
                Ok(self.__mul__(&other.inv()?))
            }

            fn serialize(&self) -> Vec<u8> {
                let mut data = vec![b'z'];
                let len = ($k as u32).to_be_bytes();
                data.extend_from_slice(&len);
                let nbytes = ($k + 7) / 8;
                let v = self.v.to_be_bytes();
                data.extend_from_slice(&v[8 - nbytes..]);
                data
            }

            fn to_json(&self) -> <Self as ToJson>::JSON {
                self.v
            }
        }
    };
}

macro_rules! gr {
    ($d: literal, $base: ty, $ty: ident, ($($reduce: expr),*), $($extra: tt)*) => {
        #[pyclass(module = "_galois_ring")]
        #[derive(Clone, Default)]
        struct $ty {
            pub(crate) elems: [$base; $d],
        }

        #[pymethods]
        impl $ty {
            #[staticmethod]
            fn base_ring(py: Python<'_>) -> Py<PyType> {
                PyType::new::<$base>(py).into()
            }

            #[staticmethod]
            fn total_degree() -> u64 {
                $d * <$base>::total_degree()
            }

            #[staticmethod]
            fn two_adicity() -> u64 {
                <$base>::two_adicity()
            }

            #[new]
            fn new(elems: &Bound<'_, PyAny>) -> PyResult<Self> {
                Ok(if elems.is_none() {
                    Self::zero()
                } else if let Ok(x) = elems.extract::<Self>() {
                    x
                }else {
                    let it = elems.try_iter()?;
                    let base: Vec<$base> = it.map(|e| e.map(|ee| <$base>::new(&ee))).flatten().collect::<PyResult<_>>()?;
                    Self {
                        elems: std::array::from_fn(|i| base.get(i).cloned().unwrap_or(<$base>::zero()))
                    }
                })
            }

            #[staticmethod]
            fn sample(rng: Bound<'_, PyAny>) -> PyResult<Self> {
                let mut res = vec![];
                for _ in (0..$d) {
                    res.push(<$base>::sample(rng.clone())?);
                }

                Ok(Self {
                    elems: res.try_into().unwrap_or_else(|_| panic!()),
                })
            }

            #[staticmethod]
            fn zero() -> Self {
                Self {
                    elems: std::array::from_fn(|_| <$base>::zero()),
                }
            }

            #[staticmethod]
            fn one() -> Self {
                Self {
                    elems: std::array::from_fn(|i| {
                        if i == 0 {
                            <$base>::one()
                        } else {
                            <$base>::zero()
                        }
                    }),
                }
            }

            #[staticmethod]
            fn exseq_size() -> usize {
                <$base>::exseq_size().pow($d)
            }

            #[staticmethod]
            fn exseq(mut i: usize) -> Self {
                let s = <$base>::exseq_size();
                Self {
                    elems: std::array::from_fn(|_| {
                        let res = <$base>::exseq(i % s);
                        i /= s;
                        res
                    }),
                }
            }

            fn is_zero(&self) -> bool {
                self.elems.iter().all(<$base>::is_zero)
            }

            fn __neg__(&self) -> Self {
                Self::zero().__sub__(self)
            }

            fn __add__(&self, other: &Self) -> Self {
                Self {
                    elems: std::array::from_fn(|i| self.elems[i].__add__(&other.elems[i])),
                }
            }

            fn __sub__(&self, other: &Self) -> Self {
                Self {
                    elems: std::array::from_fn(|i| self.elems[i].__sub__(&other.elems[i])),
                }
            }

            fn __mul__(&self, other: &Self) -> Self {
                let mut raw_mul: [$base; $d * $d - 1] = std::array::from_fn(|_| <$base>::zero());
                for i in (0..$d) {
                    for j in (0..$d) {
                        raw_mul[i + j] =
                            raw_mul[i + j].__add__(&self.elems[i].__mul__(&other.elems[j]));
                    }
                }
                let low = Self {
                    elems: std::array::from_fn(|i| raw_mul[i].clone())
                };
                let high = Self {
                    elems: std::array::from_fn(|i| raw_mul[$d + i].clone())
                };
                if high.is_zero() {
                    low
                } else {
                    Self {
                        elems: [$($reduce),*]
                    }.__mul__(&high).__add__(&low)
                }
            }

            fn inv(&self) -> Self {
                let mut res = Self::one();
                let d = Self::total_degree();
                let k = Self::two_adicity();
                let mut a = self.clone();
                for i in (0..k + d - 1) {
                    if i != k - 1 {
                        res = res.__mul__(&a);
                    }
                    a = a.__mul__(&a);
                }
                res
            }

            fn __truediv__(&self, other: &Self) -> Self {
                self.__mul__(&other.inv())
            }

            fn __pow__(&self, mut exp: u64, _m: Option<u64>) -> Self {
                let mut res = Self::one();
                let mut b = self.clone();
                while exp > 0 {
                    if exp & 1 == 1 {
                        res = res.__mul__(&b);
                    }
                    b = b.__mul__(&b);
                    exp >>= 1;
                }
                res
            }

            fn normalize(&self) -> Vec<$base> {
                let mut res = self.elems.iter().cloned().collect::<Vec<_>>();
                while !res.is_empty() && res.last().unwrap_or_else(|| panic!()).is_zero() {
                    res.pop();
                }
                res
            }

            fn serialize(&self) -> Vec<u8> {
                let elems = self.normalize();
                let mut data = vec![b'g'];
                let len = (elems.len() as u32).to_be_bytes();
                data.extend_from_slice(&len);
                for e in elems {
                    data.extend(e.serialize());
                }
                data
            }

            fn to_json(&self) -> Vec<<$base as ToJson>::JSON> {
                self.elems.iter().map(<$base>::to_json).collect()
            }

            #[getter]
            fn v(&self) -> Vec<$base> {
                self.elems.iter().cloned().collect()
            }

            $($extra)*
        }

        impl ToJson for $ty {
            type JSON = Vec<<$base as ToJson>::JSON>;
        }
    };
}

z2k!(18, Z2k18);
z2k!(32, Z2k32);
z2k!(49, Z2k49);

gr!(
    6,
    Z2k49,
    Input,
    (
        Z2k49 { v: 1 },
        Z2k49 { v: 1 },
        Z2k49 { v: 0 },
        Z2k49 { v: 0 },
        Z2k49 { v: 0 },
        Z2k49 { v: 0 }
    ),
    fn truncate(&self, py: Python<'_>, ty: Bound<'_, PyAny>) -> PyResult<Witness> {
        if Witness::base_ring(py)
            .call_method1(py, "__eq__", (ty.clone(), ty))?
            .extract::<bool>(py)?
        {
            Ok(Witness {
                elems: self.elems.clone().map(|e| Z2k32 { v: e.v }),
            })
        } else {
            Err(PyErr::new::<PyValueError, _>(
                "Can only truncate Input to Witness",
            ))
        }
    }
);

gr!(
    6,
    Z2k32,
    Witness,
    (
        Z2k32 { v: 1 },
        Z2k32 { v: 1 },
        Z2k32 { v: 0 },
        Z2k32 { v: 0 },
        Z2k32 { v: 0 },
        Z2k32 { v: 0 }
    ),
);

gr!(
    4,
    Witness,
    Check,
    (
        Witness {
            elems: [
                Z2k32 { v: 0 },
                Z2k32 { v: 1 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 }
            ]
        },
        Witness {
            elems: [
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 1 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 }
            ]
        },
        Witness {
            elems: [
                Z2k32 { v: 0 },
                Z2k32 { v: 1 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 }
            ]
        },
        Witness {
            elems: [
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 },
                Z2k32 { v: 0 }
            ]
        }
    ),
);

/// A Python module implemented in Rust.
#[pymodule]
fn _galois_ring(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Z2k18>()?;
    m.add_class::<Z2k32>()?;
    m.add_class::<Z2k49>()?;
    m.add_class::<Input>()?;
    m.add_class::<Witness>()?;
    m.add_class::<Check>()?;
    Ok(())
}
