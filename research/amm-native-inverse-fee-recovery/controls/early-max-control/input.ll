; ModuleID = 'input.d4101c9815407191-cgu.0'
source_filename = "input.d4101c9815407191-cgu.0"
target datalayout = "e-m:e-p:64:64-i64:64-n32:64-S128"
target triple = "sbf"

; Function Attrs: mustprogress nofree norecurse nosync nounwind willreturn memory(argmem: read)
define { i64, i64 } @inverse_return(ptr noalias nocapture noundef readonly align 8 dereferenceable(24) %fee, i64 noundef %amount) unnamed_addr #0 {
start:
  %0 = getelementptr inbounds i8, ptr %fee, i64 8
  %max = load i64, ptr %0, align 8, !noundef !2
  %1 = getelementptr inbounds i8, ptr %fee, i64 16
  %_5 = load i16, ptr %1, align 8, !noundef !2
  %bps = zext i16 %_5 to i128
  %2 = icmp eq i16 %_5, 0
  br i1 %2, label %bb16, label %bb2

bb2:                                              ; preds = %start
  %3 = icmp eq i64 %amount, 0
  br i1 %3, label %bb16, label %bb4

bb16:                                             ; preds = %bb8, %bb24, %bb6, %bb5, %bb2, %start, %bb38, %bb9, %bb19
  %_0.sroa.15.0 = phi i64 [ %_31.0, %bb19 ], [ %_58.0, %bb38 ], [ %_60, %bb9 ], [ %amount, %start ], [ 0, %bb2 ], [ undef, %bb5 ], [ undef, %bb6 ], [ undef, %bb24 ], [ undef, %bb8 ]
  %_0.sroa.0.0 = phi i64 [ 1, %bb19 ], [ 1, %bb38 ], [ %_0.sroa.0.2, %bb9 ], [ 1, %start ], [ 1, %bb2 ], [ 0, %bb5 ], [ 0, %bb6 ], [ 0, %bb24 ], [ 0, %bb8 ]
  %4 = insertvalue { i64, i64 } poison, i64 %_0.sroa.0.0, 0
  %5 = insertvalue { i64, i64 } %4, i64 %_0.sroa.15.0, 1
  ret { i64, i64 } %5

bb4:                                              ; preds = %bb2
  %6 = icmp eq i16 %_5, 10000
  br i1 %6, label %bb5, label %bb6

bb5:                                              ; preds = %bb4
  %7 = tail call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %max, i64 %amount)
  %_31.1 = extractvalue { i64, i1 } %7, 1
  br i1 %_31.1, label %bb16, label %bb19

bb6:                                              ; preds = %bb4
  %_8 = zext i64 %amount to i128
  %_37 = icmp ult i16 %_5, 10001
  br i1 %_37, label %bb24, label %bb16

bb19:                                             ; preds = %bb5
  %_31.0 = extractvalue { i64, i1 } %7, 0
  br label %bb16

bb24:                                             ; preds = %bb6
  %8 = mul nuw nsw i128 %_8, 10000
  %_38 = sub nuw nsw i128 10000, %bps
  %9 = sub nsw i128 %8, %bps
  %_46 = add nsw i128 %9, 9999
  %_50 = udiv i128 %_46, %_38
  %_52.not = icmp ult i128 %_50, %_8
  br i1 %_52.not, label %bb16, label %bb34

bb34:                                             ; preds = %bb24
  %_53 = sub nuw nsw i128 %_50, %_8
  %_26 = zext i64 %max to i128
  %_22.not = icmp ult i128 %_53, %_26
  br i1 %_22.not, label %bb9, label %bb8

bb9:                                              ; preds = %bb34
  %_59 = icmp ult i128 %_50, 18446744073709551616
  %_60 = trunc i128 %_50 to i64
  %_0.sroa.0.2 = zext i1 %_59 to i64
  br label %bb16

bb8:                                              ; preds = %bb34
  %10 = tail call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %amount, i64 %max)
  %_58.1 = extractvalue { i64, i1 } %10, 1
  br i1 %_58.1, label %bb16, label %bb38

bb38:                                             ; preds = %bb8
  %_58.0 = extractvalue { i64, i1 } %10, 0
  br label %bb16
}

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare hidden { i64, i1 } @llvm.uadd.with.overflow.i64(i64, i64) #1

attributes #0 = { mustprogress nofree norecurse nosync nounwind willreturn memory(argmem: read) "target-cpu"="generic" "target-features"="+store-imm,+jmp-ext" }
attributes #1 = { mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 8, !"PIC Level", i32 2}
!1 = !{!"rustc version 1.79.0-dev"}
!2 = !{}
