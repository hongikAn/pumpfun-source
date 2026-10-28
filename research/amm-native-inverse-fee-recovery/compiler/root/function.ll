define hidden void @_ZN18pump_amm_recovered5utils12transfer_fee17amount_before_fee17h2c1d02fd8f1c202fE(ptr dead_on_unwind noalias nocapture noundef writable writeonly sret([16 x i8]) align 8 dereferenceable(16) %_0, ptr noalias nocapture noundef readonly align 8 dereferenceable(32) %data, i64 noundef %amount) unnamed_addr #1 {
start:
  %_11.i.i = alloca [0 x i8], align 1
  %formatter.i.i = alloca [64 x i8], align 8
  %buf.i.i = alloca [24 x i8], align 8
  %_3.i = alloca [24 x i8], align 8
  %_2.i = alloca [160 x i8], align 8
  %fee = alloca [24 x i8], align 8
  %_3 = load i64, ptr %data, align 8, !range !352, !noundef !2
  %trunc.not = icmp eq i64 %_3, 0
  br i1 %trunc.not, label %bb3, label %bb2

bb3:                                              ; preds = %start
  %0 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %amount, ptr %0, align 8
  store i64 2, ptr %_0, align 8
  br label %bb5

bb2:                                              ; preds = %start
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %fee)
  %1 = getelementptr inbounds i8, ptr %data, i64 8
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %fee, ptr noundef nonnull align 8 dereferenceable(24) %1, i64 24, i1 false)
; call native_transfer_fee::DecodedTransferFee::calculate_pre_fee_amount
  %2 = call { i64, i64 } @_ZN19native_transfer_fee18DecodedTransferFee24calculate_pre_fee_amount17hd5a2ad6e6f9aa53bE(ptr noalias noundef nonnull readonly align 8 dereferenceable(24) %fee, i64 noundef %amount) #34
  %3 = extractvalue { i64, i64 } %2, 0
  %switch1 = icmp eq i64 %3, 0
  br i1 %switch1, label %bb7, label %bb8

bb5:                                              ; preds = %bb6, %bb3
  ret void

bb7:                                              ; preds = %bb2
  call void @llvm.lifetime.start.p0(i64 160, ptr nonnull %_2.i)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %_3.i)
; call pump_amm_recovered::PumpAmmError::name
  call void @_ZN18pump_amm_recovered12PumpAmmError4name17h7a0105055247a4bfE(ptr noalias nocapture noundef nonnull sret([24 x i8]) align 8 dereferenceable(24) %_3.i, ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1f1600f67af89fc229573eafc1a3b5f5) #34
  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i.i)
  call void @llvm.lifetime.start.p0(i64 24, ptr nonnull %buf.i.i), !noalias !4532
  store i64 0, ptr %buf.i.i, align 8, !noalias !4532
  %_9.sroa.4.0.buf.sroa_idx.i.i = getelementptr inbounds i8, ptr %buf.i.i, i64 8
  store ptr inttoptr (i64 1 to ptr), ptr %_9.sroa.4.0.buf.sroa_idx.i.i, align 8, !noalias !4532
  %_9.sroa.5.0.buf.sroa_idx.i.i = getelementptr inbounds i8, ptr %buf.i.i, i64 16
  store i64 0, ptr %_9.sroa.5.0.buf.sroa_idx.i.i, align 8, !noalias !4532
  call void @llvm.lifetime.start.p0(i64 64, ptr nonnull %formatter.i.i), !noalias !4532
  %4 = getelementptr inbounds i8, ptr %formatter.i.i, i64 52
  store i32 0, ptr %4, align 4, !noalias !4532
  %5 = getelementptr inbounds i8, ptr %formatter.i.i, i64 48
  store i32 32, ptr %5, align 8, !noalias !4532
  %6 = getelementptr inbounds i8, ptr %formatter.i.i, i64 56
  store i8 3, ptr %6, align 8, !noalias !4532
  store i64 0, ptr %formatter.i.i, align 8, !noalias !4532
  %7 = getelementptr inbounds i8, ptr %formatter.i.i, i64 16
  store i64 0, ptr %7, align 8, !noalias !4532
  %8 = getelementptr inbounds i8, ptr %formatter.i.i, i64 32
  store ptr %buf.i.i, ptr %8, align 8, !noalias !4532
  %9 = getelementptr inbounds i8, ptr %formatter.i.i, i64 40
  store ptr @vtable.3, ptr %9, align 8, !noalias !4532
; call <pump_amm_recovered::PumpAmmError as core::fmt::Display>::fmt
  %10 = call noundef zeroext i1 @"_ZN71_$LT$pump_amm_recovered..PumpAmmError$u20$as$u20$core..fmt..Display$GT$3fmt17h2aa5cc74834c3184E"(ptr noalias noundef nonnull readonly align 4 dereferenceable(4) @alloc_1f1600f67af89fc229573eafc1a3b5f5, ptr noalias noundef nonnull align 8 dereferenceable(64) %formatter.i.i) #34, !noalias !4536
  br i1 %10, label %bb3.i.i, label %"_ZN18pump_amm_recovered5utils12transfer_fee17amount_before_fee28_$u7b$$u7b$closure$u7d$$u7d$17h86a722525afe071fE.exit"

bb3.i.i:                                          ; preds = %bb7
; call core::result::unwrap_failed
  call void @_ZN4core6result13unwrap_failed17h2dbd2ef42161686dE(ptr noalias noundef nonnull readonly align 1 @alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55, ptr noundef nonnull align 1 %_11.i.i, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @vtable.4, ptr noalias noundef nonnull readonly align 8 dereferenceable(24) @alloc_d5d9fccaf545b6e0545ef73245a3c43f) #35, !noalias !4532
  unreachable

"_ZN18pump_amm_recovered5utils12transfer_fee17amount_before_fee28_$u7b$$u7b$closure$u7d$$u7d$17h86a722525afe071fE.exit": ; preds = %bb7
  %11 = getelementptr inbounds i8, ptr %_2.i, i64 56
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %11, ptr noundef nonnull align 8 dereferenceable(24) %buf.i.i, i64 24, i1 false)
  call void @llvm.lifetime.end.p0(i64 64, ptr nonnull %formatter.i.i), !noalias !4532
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %buf.i.i), !noalias !4532
  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i.i)
  %12 = getelementptr inbounds i8, ptr %_2.i, i64 32
  call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 8 dereferenceable(24) %12, ptr noundef nonnull align 8 dereferenceable(24) %_3.i, i64 24, i1 false)
  %13 = getelementptr inbounds i8, ptr %_2.i, i64 152
  store i32 6023, ptr %13, align 8
  store i64 0, ptr %_2.i, align 8
  %_6.sroa.4.0._2.sroa_idx.i = getelementptr inbounds i8, ptr %_2.i, i64 8
  store ptr @alloc_b6d410389d832d2a4196b7c019a28dd2, ptr %_6.sroa.4.0._2.sroa_idx.i, align 8
  %_6.sroa.4.sroa.4.0._6.sroa.4.0._2.sroa_idx.sroa_idx.i = getelementptr inbounds i8, ptr %_2.i, i64 16
  store i64 43, ptr %_6.sroa.4.sroa.4.0._6.sroa.4.0._2.sroa_idx.sroa_idx.i, align 8
  %_6.sroa.4.sroa.5.0._6.sroa.4.0._2.sroa_idx.sroa_idx.i = getelementptr inbounds i8, ptr %_2.i, i64 24
  store i32 67, ptr %_6.sroa.4.sroa.5.0._6.sroa.4.0._2.sroa_idx.sroa_idx.i, align 8
  %14 = getelementptr inbounds i8, ptr %_2.i, i64 80
  store i8 2, ptr %14, align 8
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %_3.i)
; call <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from
  %15 = call { i64, ptr } @"_ZN104_$LT$anchor_lang..error..Error$u20$as$u20$core..convert..From$LT$anchor_lang..error..AnchorError$GT$$GT$4from17hefc4a4c4d9276c8eE"(ptr noalias nocapture noundef nonnull readonly align 8 dereferenceable(160) %_2.i) #34
  call void @llvm.lifetime.end.p0(i64 160, ptr nonnull %_2.i)
  %_9.0 = extractvalue { i64, ptr } %15, 0
  %_9.1 = extractvalue { i64, ptr } %15, 1
  store i64 %_9.0, ptr %_0, align 8
  %16 = getelementptr inbounds i8, ptr %_0, i64 8
  store ptr %_9.1, ptr %16, align 8
  br label %bb6

bb8:                                              ; preds = %bb2
  %17 = extractvalue { i64, i64 } %2, 1
  %18 = getelementptr inbounds i8, ptr %_0, i64 8
  store i64 %17, ptr %18, align 8
  store i64 2, ptr %_0, align 8
  br label %bb6

bb6:                                              ; preds = %bb8, %"_ZN18pump_amm_recovered5utils12transfer_fee17amount_before_fee28_$u7b$$u7b$closure$u7d$$u7d$17h86a722525afe071fE.exit"
  call void @llvm.lifetime.end.p0(i64 24, ptr nonnull %fee)
  br label %bb5
}
