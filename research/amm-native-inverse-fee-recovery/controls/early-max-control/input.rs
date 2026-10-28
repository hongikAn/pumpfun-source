#![no_std]
#[derive(Clone,Copy,Debug)]
pub struct DecodedTransferFee {pub epoch:u64,pub maximum_fee:u64,pub transfer_fee_basis_points:u16}
#[no_mangle]
pub fn inverse_return(fee:&DecodedTransferFee, amount:u64)->Option<u64> {
    let max=fee.maximum_fee; let bps=fee.transfer_fee_basis_points as u128;
    if bps==0{return Some(amount);} if amount==0{return Some(0);} if bps==10000{return max.checked_add(amount);}
    let n=(amount as u128).checked_mul(10000)?;let d=10000u128.checked_sub(bps)?;let raw=n.checked_add(d)?.checked_sub(1)?.checked_div(d)?;
    if raw.checked_sub(amount as u128)? >= max as u128 {amount.checked_add(max)}else{u64::try_from(raw).ok()}
}
