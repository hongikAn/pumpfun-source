#![no_std]

#[derive(Clone, Copy, Debug)]
pub struct DecodedTransferFee {
    pub epoch: u64,
    pub maximum_fee: u64,
    pub transfer_fee_basis_points: u16,
}

impl DecodedTransferFee {
    #[inline(never)]
pub fn calculate_fee(&self, amount:u64)->Option<u64> {
    if amount==0 {return Some(0); }
    let bps=self.transfer_fee_basis_points as u128;
    if bps==0 { return Some(0); }
    let n=(amount as u128).checked_mul(bps)?;
    let raw=n.checked_add(10000)?.checked_sub(1)?.checked_div(10000)?.try_into().ok()?;
    Some(core::cmp::min(raw,self.maximum_fee))
}
    #[inline(never)]
pub fn calculate_pre_fee_amount(&self, amount:u64)->Option<u64> {
    let bps=self.transfer_fee_basis_points as u128;
    if bps==0{return Some(amount);} if amount==0{return Some(0);} if bps==10000{return self.maximum_self.checked_add(amount);}
    let n=(amount as u128).checked_mul(10000)?;let d=10000u128.checked_sub(bps)?;let raw=n.checked_add(d)?.checked_sub(1)?.checked_div(d)?;
    if raw.checked_sub(amount as u128)? >= self.maximum_fee as u128 {amount.checked_add(self.maximum_fee)}else{u64::try_from(raw).ok()}
}
}
