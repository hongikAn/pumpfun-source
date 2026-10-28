define hidden { i64, i64 } @_ZN19native_transfer_fee18DecodedTransferFee24calculate_pre_fee_amount17hd5a2ad6e6f9aa53bE(ptr noalias nocapture noundef readonly align 8 dereferenceable(24) %self, i64 noundef %amount) unnamed_addr #0 {
start:
  %0 = getelementptr inbounds i8, ptr %self, i64 16
  %_4 = load i16, ptr %0, align 8, !noundef !2
  %bps = zext i16 %_4 to i128
  %1 = icmp eq i16 %_4, 0
  br i1 %1, label %bb16, label %bb2

bb2:                                              ; preds = %start
  %2 = icmp eq i64 %amount, 0
  br i1 %2, label %bb16, label %bb4

bb16:                                             ; preds = %bb8, %bb24, %bb6, %bb5, %bb2, %start, %bb38, %bb9, %bb19
  %_0.sroa.15.0 = phi i64 [ %_32.0, %bb19 ], [ %_59.0, %bb38 ], [ %_61, %bb9 ], [ %amount, %start ], [ 0, %bb2 ], [ undef, %bb5 ], [ undef, %bb6 ], [ undef, %bb24 ], [ undef, %bb8 ]
  %_0.sroa.0.0 = phi i64 [ 1, %bb19 ], [ 1, %bb38 ], [ %_0.sroa.0.2, %bb9 ], [ 1, %start ], [ 1, %bb2 ], [ 0, %bb5 ], [ 0, %bb6 ], [ 0, %bb24 ], [ 0, %bb8 ]
  %3 = insertvalue { i64, i64 } poison, i64 %_0.sroa.0.0, 0
  %4 = insertvalue { i64, i64 } %3, i64 %_0.sroa.15.0, 1
  ret { i64, i64 } %4

bb4:                                              ; preds = %bb2
  %5 = icmp eq i16 %_4, 10000
  br i1 %5, label %bb5, label %bb6

bb5:                                              ; preds = %bb4
  %6 = getelementptr inbounds i8, ptr %self, i64 8
  %_5 = load i64, ptr %6, align 8, !noundef !2
  %7 = tail call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %_5, i64 %amount)
  %_32.1 = extractvalue { i64, i1 } %7, 1
  br i1 %_32.1, label %bb16, label %bb19

bb6:                                              ; preds = %bb4
  %_8 = zext i64 %amount to i128
  %_38 = icmp ult i16 %_4, 10001
  br i1 %_38, label %bb24, label %bb16

bb19:                                             ; preds = %bb5
  %_32.0 = extractvalue { i64, i1 } %7, 0
  br label %bb16

bb24:                                             ; preds = %bb6
  %8 = mul nuw nsw i128 %_8, 10000
  %_39 = sub nuw nsw i128 10000, %bps
  %9 = sub nsw i128 %8, %bps
  %_47 = add nsw i128 %9, 9999
  %_51 = udiv i128 %_47, %_39
  %_53.not = icmp ult i128 %_51, %_8
  br i1 %_53.not, label %bb16, label %bb34

bb34:                                             ; preds = %bb24
  %_54 = sub nuw nsw i128 %_51, %_8
  %10 = getelementptr inbounds i8, ptr %self, i64 8
  %_27 = load i64, ptr %10, align 8, !noundef !2
  %_26 = zext i64 %_27 to i128
  %_22.not = icmp ult i128 %_54, %_26
  br i1 %_22.not, label %bb9, label %bb8

bb9:                                              ; preds = %bb34
  %_60 = icmp ult i128 %_51, 18446744073709551616
  %_61 = trunc i128 %_51 to i64
  %_0.sroa.0.2 = zext i1 %_60 to i64
  br label %bb16

bb8:                                              ; preds = %bb34
  %11 = tail call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %amount, i64 %_27)
  %_59.1 = extractvalue { i64, i1 } %11, 1
  br i1 %_59.1, label %bb16, label %bb38

bb38:                                             ; preds = %bb8
  %_59.0 = extractvalue { i64, i1 } %11, 0
  br label %bb16
}
